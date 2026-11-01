import contextlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


manage = load('release_manage', ROOT / 'manage.py')
builder = load('release_builder', ROOT / 'scripts/build_release.py')


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'instance with spaces'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns(
            '.git', 'dist', '__pycache__', 'data', 'napcat', 'logs', 'backups'))

    def tearDown(self):
        self.temp.cleanup()

    def test_release_excludes_runtime_data_and_is_reproducible(self):
        marker = 'PRIVATE-NOT-FOR-PUBLICATION-93842'
        for name in ['data/cmd_config.json', 'napcat/qq/session', '.env', 'credentials.txt',
                     'logs/first-run.log', 'backups/private.tar.gz']:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(marker, encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            first = builder.build(self.root, self.root / 'dist1')
            second = builder.build(self.root, self.root / 'dist2')
        self.assertEqual([p.read_bytes() for p in first], [p.read_bytes() for p in second])
        with tarfile.open(first[0]) as archive:
            names = archive.getnames()
            self.assertIn('aiassistrobot-linux/first-run.sh', names)
            self.assertIn('aiassistrobot-linux/docs/INSTALL_LINUX.md', names)
            for member in archive.getmembers():
                if member.isfile():
                    payload = archive.extractfile(member).read()
                    self.assertNotIn(marker.encode(), payload)
                    if member.name.endswith('.sh'):
                        self.assertNotIn(b'\r\n', payload)
        with zipfile.ZipFile(first[1]) as archive:
            self.assertIn('aiassistrobot-windows/setup.cmd', archive.namelist())
            self.assertIn('aiassistrobot-windows/docs/INSTALL_WINDOWS.md', archive.namelist())
            for name in archive.namelist():
                payload = archive.read(name)
                self.assertNotIn(marker.encode(), payload)
                self.assertNotIn('wechat-setup', name)
                if name.endswith('.cmd'):
                    self.assertIn(b'\r\n', payload)
                    self.assertNotIn(b'\r\r\n', payload)

    def test_first_run_logs_hidden_key_only_to_configuration(self):
        key = 'test-private-sentinel-not-in-process-log'
        answers = iter(['123456789', '', 'n', '', ''])
        def fake_compose(*args, capture=False):
            return SimpleNamespace(stdout='container startup example\n')
        with patch.object(manage, 'ROOT', self.root), \
                patch.object(manage, 'preflight'), \
                patch.object(manage, 'wait_web'), \
                patch.object(manage, 'compose', fake_compose), \
                patch.object(manage, 'doctor', return_value=0), \
                patch.object(manage, 'hidden_key', return_value=key), \
                patch('builtins.input', side_effect=lambda _: next(answers)), \
                contextlib.redirect_stdout(io.StringIO()):
            code = manage.first_run(SimpleNamespace(no_pull=False))
        self.assertEqual(code, 0)
        conf = json.loads((self.root / 'data/cmd_config.json').read_text(encoding='utf-8'))
        self.assertEqual(conf['provider_sources'][0]['key'], [key])
        self.assertIn('READY_AWAITING_QQ_LOGIN', (self.root / 'logs/first-run.status').read_text())
        for logfile in (self.root / 'logs').glob('*.log'):
            self.assertNotIn(key, logfile.read_text(encoding='utf-8'))

    def test_failed_first_run_saves_error_and_failure_status(self):
        with patch.object(manage, 'ROOT', self.root), \
                patch.object(manage, 'setup', side_effect=ValueError('preflight failed')), \
                patch.object(manage, 'compose', side_effect=OSError('docker missing')), \
                contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(ValueError):
                manage.first_run(SimpleNamespace(no_pull=False))
        self.assertIn('FAILED', (self.root / 'logs/first-run.status').read_text())
        logfile = next((self.root / 'logs').glob('first-run-*.log'))
        self.assertIn('preflight failed', logfile.read_text(encoding='utf-8'))

    def test_wrong_container_engine_refuses_before_writing_user_config(self):
        with patch.object(manage, 'ROOT', self.root), \
                patch.object(manage.shutil, 'which', return_value='docker'), \
                patch.object(manage, 'compose'), \
                patch.object(manage.subprocess, 'run', return_value=SimpleNamespace(stdout='windows\n')):
            with self.assertRaisesRegex(ValueError, 'Linux'):
                manage.preflight()
        self.assertFalse((self.root / 'data').exists())

    def test_doctor_fails_for_unavailable_model(self):
        manage.init(self.root, '123456789', 'test-key', model='not-present')
        response = io.StringIO('{"data":[{"id":"deepseek-flash"}]}')
        with patch.object(manage, 'ROOT', self.root), \
                patch.object(manage, 'compose'), \
                patch.object(manage, 'wait_web'), \
                patch.object(manage.urllib.request, 'urlopen', return_value=response), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(manage.doctor(), 1)

    def test_backup_has_both_system_entry_points_and_can_be_unpacked(self):
        manage.init(self.root, '123456789', 'test-private-key')
        with patch.object(manage, 'ROOT', self.root), \
                patch.object(manage, 'compose', return_value=SimpleNamespace(stdout='astrbot\nnapcat\n')), \
                contextlib.redirect_stdout(io.StringIO()):
            manage.backup()
        backup = next((self.root / 'backups').glob('*.tar.gz'))
        with tarfile.open(backup) as archive:
            names = archive.getnames()
            for name in ['first-run.sh', 'setup.cmd', 'manage.ps1', 'data/cmd_config.json',
                         'data/dafeiyu/settings.json', 'napcat/config/onebot11.json']:
                self.assertIn('aiassistrobot/' + name, names)
            # Read back the archived configuration, without executing it.
            payload = json.load(archive.extractfile('aiassistrobot/data/cmd_config.json'))
            self.assertEqual(payload['provider_sources'][0]['key'], ['test-private-key'])

    @unittest.skipUnless(shutil.which('powershell.exe'), 'Windows wrapper check')
    def test_windows_wrapper_handles_spaces_and_preserves_exit_code(self):
        result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                                 '-File', str(self.root / 'manage.ps1'), 'status'],
                                capture_output=True, timeout=30)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse((self.root / 'data').exists())


if __name__ == '__main__':
    unittest.main()
