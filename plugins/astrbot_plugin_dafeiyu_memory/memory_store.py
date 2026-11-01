"""Small persistent fact store; intentionally independent of AstrBot."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def memory_scope(settings, platform, sender, group=''):
    platform, sender, group = str(platform), str(sender), str(group or '')
    if platform != 'qq':
        return None  # Phase one deliberately supports only the QQ adapter.
    if group:
        if group not in {str(g) for g in settings.get('allowed_groups', [])}:
            return None
        return f'{platform}:group:{group}:member:{sender}'
    users = {str(u) for u in settings.get('allowed_users', [])}
    users.add(str(settings['owner_qq']))
    return f'{platform}:{sender}' if sender in users else None


class MemoryStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS facts (
                    id INTEGER PRIMARY KEY, scope TEXT NOT NULL,
                    name TEXT NOT NULL, value TEXT NOT NULL, manual INTEGER NOT NULL,
                    updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(scope, name));
                CREATE TABLE IF NOT EXISTS pending (
                    id INTEGER PRIMARY KEY, scope TEXT NOT NULL,
                    message_id TEXT NOT NULL, text TEXT NOT NULL,
                    UNIQUE(scope, message_id));
            ''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        try:
            with db:
                yield db
        finally:
            db.close()

    def put(self, scope, name, value, manual=True):
        name, value = str(name).strip()[:80], str(value).strip()[:400]
        if not name or not value:
            return False
        with self.connect() as db:
            old = db.execute('SELECT manual FROM facts WHERE scope=? AND name=?',
                             (scope, name)).fetchone()
            if old and old[0] and not manual:
                return False  # automatic extraction cannot overwrite an explicit note
            if not old and db.execute('SELECT COUNT(*) FROM facts WHERE scope=?',
                                      (scope,)).fetchone()[0] >= 80:
                return False
            db.execute('''INSERT INTO facts(scope,name,value,manual) VALUES(?,?,?,?)
                ON CONFLICT(scope,name) DO UPDATE SET value=excluded.value,
                manual=excluded.manual, updated=CURRENT_TIMESTAMP''',
                       (scope, name, value, int(manual)))
        return True

    def list(self, scope):
        with self.connect() as db:
            return db.execute('SELECT id,name,value,manual FROM facts WHERE scope=? '
                              'ORDER BY manual DESC,updated DESC,id DESC', (scope,)).fetchall()

    def recall(self, scope, query, limit=12):
        def grams(text):
            return {text[i:i+2] for i in range(max(0, len(text)-1))}
        q = grams(query.lower())
        rows = self.list(scope)
        rows.sort(key=lambda r: len(q & grams((r[1]+r[2]).lower())), reverse=True)
        return rows[:limit]

    def forget(self, scope, number):
        with self.connect() as db:
            return db.execute('DELETE FROM facts WHERE scope=? AND id=?',
                              (scope, number)).rowcount > 0

    def enqueue(self, scope, message_id, text):
        with self.connect() as db:
            db.execute('INSERT OR IGNORE INTO pending(scope,message_id,text) VALUES(?,?,?)',
                       (scope, message_id, text[:2000]))

    def batch(self, scope):
        with self.connect() as db:
            return db.execute('SELECT id,text FROM pending WHERE scope=? ORDER BY id LIMIT 16',
                              (scope,)).fetchall()

    def finish_batch(self, scope, last_id):
        with self.connect() as db:
            db.execute('DELETE FROM pending WHERE scope=? AND id<=?', (scope, last_id))


def parse_facts(text):
    raw = text.strip()
    if raw.startswith('```'):
        raw = raw.split('\n', 1)[1].rsplit('```', 1)[0].strip()
    result = json.loads(raw)
    if not isinstance(result, list) or len(result) > 8:
        raise ValueError('Expected at most eight memory facts')
    for fact in result:
        if not isinstance(fact, dict) or set(fact) != {'name', 'value'}:
            raise ValueError('Invalid memory fact')
        if not all(isinstance(fact[k], str) and fact[k].strip() for k in fact):
            raise ValueError('Memory fact must contain nonempty strings')
    return result
