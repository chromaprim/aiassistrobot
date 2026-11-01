import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import tarfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


manage = module('manage', ROOT / 'manage.py')
memory = module('memory_store', ROOT / 'plugins/astrbot_plugin_dafeiyu_memory/memory_store.py')


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'plugins', self.root / 'plugins')
        shutil.copyfile(ROOT / 'persona.txt', self.root / 'persona.txt')

    def tearDown(self):
        self.temp.cleanup()

    def test_init_tokens_and_literal_key(self):
        key = 'test-$(`literal`)-key'
        manage.init(self.root, '123456789', key)
        config = json.loads((self.root / 'data/cmd_config.json').read_text(encoding='utf-8'))
        nap = json.loads((self.root / 'napcat/config/onebot11.json').read_text(encoding='utf-8'))
        self.assertEqual(config['provider_sources'][0]['key'], [key])
        self.assertEqual(config['platform'][0]['ws_reverse_token'], nap['network']['websocketClients'][0]['token'])
        self.assertEqual(config['agent_runner']['config']['model']['provider_id'], config['provider'][0]['id'])
        self.assertEqual(config['platform_settings']['id_whitelist'], ['qq:FriendMessage:123456789'])
        self.assertFalse(config['platform_settings']['wl_ignore_admin_on_group'])

    def test_init_is_not_destructive(self):
        manage.init(self.root, '123456789', 'test-key')
        before = (self.root / 'data/cmd_config.json').read_bytes()
        with self.assertRaises(ValueError):
            manage.init(self.root, '987654321', 'another-key')
        self.assertEqual(before, (self.root / 'data/cmd_config.json').read_bytes())

    def test_validation_before_writing(self):
        with self.assertRaises(ValueError):
            manage.init(self.root, '../invalid', 'key')
        self.assertFalse((self.root / 'data').exists())

    def test_multiple_users_groups_and_admin_separation(self):
        manage.init(self.root, '123456789', 'test-key', users=['223456789'], groups=['88888888'])
        conf = json.loads((self.root / 'data/cmd_config.json').read_text(encoding='utf-8'))
        self.assertEqual(conf['admins_id'], ['123456789'])
        self.assertEqual(conf['platform_settings']['id_whitelist'],
                         ['qq:FriendMessage:123456789', 'qq:FriendMessage:223456789', '88888888'])
        self.assertTrue(conf['platform_settings']['unique_session'])
        settings = json.loads((self.root / 'data/dafeiyu/settings.json').read_text(encoding='utf-8'))
        scopes = [memory.memory_scope(settings, 'qq', '123456789'),
                  memory.memory_scope(settings, 'qq', '223456789'),
                  memory.memory_scope(settings, 'qq', '123456789', '88888888'),
                  memory.memory_scope(settings, 'qq', '223456789', '88888888')]
        self.assertEqual(len(set(scopes)), 4)
        self.assertIsNone(memory.memory_scope(settings, 'qq', '323456789'))
        self.assertIsNone(memory.memory_scope(settings, 'qq', '123456789', '99999999'))
        self.assertEqual(manage.parse_ids('123456789，223456789 123456789'), ['123456789', '223456789'])

    def test_access_update_preserves_key_and_memories(self):
        manage.init(self.root, '123456789', 'test-key')
        store = memory.MemoryStore(self.root / 'data/dafeiyu/memory.sqlite3')
        store.put('qq:123456789', '昵称', '小明')
        manage.update_access(self.root, ['223456789'], ['88888888'])
        self.assertEqual(store.list('qq:123456789')[0][2], '小明')
        conf = json.loads((self.root / 'data/cmd_config.json').read_text(encoding='utf-8'))
        self.assertEqual(conf['provider_sources'][0]['key'], ['test-key'])

    def test_framework_config_utf8_bom_is_supported(self):
        manage.init(self.root, '123456789', 'test-key')
        path = self.root / 'data/cmd_config.json'
        text = path.read_text(encoding='utf-8')
        path.write_text(text, encoding='utf-8-sig')
        manage.update_access(self.root, ['223456789'], ['88888888'])
        conf = json.loads(path.read_text(encoding='utf-8-sig'))
        self.assertIn('88888888', conf['platform_settings']['id_whitelist'])

    def test_reopen_and_migrate(self):
        store = memory.MemoryStore(self.root / 'original/memory.sqlite3')
        self.assertTrue(store.put('qq:owner', '昵称', '小明'))
        shutil.copytree(self.root / 'original', self.root / 'migrated')
        migrated = memory.MemoryStore(self.root / 'migrated/memory.sqlite3')
        self.assertEqual(migrated.recall('qq:owner', '我叫什么')[0][2], '小明')
        self.assertEqual(migrated.list('qq:other'), [])

    def test_manual_notes_protected_and_deletion_scoped(self):
        store = memory.MemoryStore(self.root / 'memory.sqlite3')
        store.put('owner', '昵称', '小明')
        self.assertFalse(store.put('owner', '昵称', '小王', manual=False))
        number = store.list('owner')[0][0]
        self.assertFalse(store.forget('other', number))
        self.assertTrue(store.forget('owner', number))
        self.assertEqual(store.list('owner'), [])

    def test_queue_retries_and_concurrent_arrivals(self):
        store = memory.MemoryStore(self.root / 'memory.sqlite3')
        store.enqueue('owner', 'a', '我喜欢蓝色')
        store.enqueue('owner', 'a', '重复事件')
        batch = store.batch('owner')
        self.assertEqual(len(batch), 1)
        store.enqueue('owner', 'b', '我喜欢猫')
        store.finish_batch('owner', batch[-1][0])
        self.assertEqual(store.batch('owner')[0][1], '我喜欢猫')

    def test_recall_limits_and_fact_parsing(self):
        store = memory.MemoryStore(self.root / 'memory.sqlite3')
        for i in range(80):
            self.assertTrue(store.put('owner', str(i), '普通资料' + str(i)))
        self.assertFalse(store.put('owner', 'extra', '超过容量'))
        store.put('owner', '0', '喜欢蓝色')
        self.assertEqual(store.recall('owner', '蓝色')[0][2], '喜欢蓝色')
        self.assertEqual(len(store.recall('owner', '蓝色')), 12)
        self.assertEqual(memory.parse_facts('```json\n[{"name":"昵称","value":"小明"}]\n```')[0]['value'], '小明')
        with self.assertRaises(ValueError):
            memory.parse_facts('{"name":"昵称"}')

    def test_backup_includes_memory_and_restores_only_running_services(self):
        manage.init(self.root, '123456789', 'test-key')
        memory.MemoryStore(self.root / 'data/dafeiyu/memory.sqlite3').put('qq:owner', '昵称', '小明')
        for name in ['manage.py', 'compose.yaml', 'setup.sh']:
            shutil.copyfile(ROOT / name, self.root / name)
        calls = []
        def fake_compose(*args, capture=False):
            calls.append(args)
            return SimpleNamespace(stdout='astrbot\n')
        with patch.object(manage, 'ROOT', self.root), patch.object(manage, 'compose', fake_compose):
            manage.backup()
        archives = list((self.root / 'backups').glob('*.tar.gz'))
        self.assertEqual(len(archives), 1)
        self.assertEqual(list((self.root / 'backups').glob('*.partial')), [])
        with tarfile.open(archives[0]) as archive:
            self.assertIn('aiassistrobot/data/dafeiyu/memory.sqlite3', archive.getnames())
            self.assertIn('aiassistrobot/data/cmd_config.json', archive.getnames())
        self.assertEqual(calls[-1], ('start', 'astrbot'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
