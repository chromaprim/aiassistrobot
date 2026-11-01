#!/usr/bin/env python3
"""Portable deployment manager. Standard library only; Python >=3.9."""
import argparse
import datetime
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tarfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
VERSION = '1.0.0'


class Tee:
    """Keep interactive input attached to the terminal; record program output."""
    def __init__(self, terminal, log):
        self.terminal, self.log = terminal, log

    def write(self, text):
        self.terminal.write(text)
        self.log.write(text)
        self.flush()
        return len(text)

    def flush(self):
        self.terminal.flush()
        self.log.flush()

    def isatty(self):
        return self.terminal.isatty()


def hidden_key():
    # Never fall back to echoed input when started without a real terminal.
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        return getpass.getpass('DeepSeek API Key（隐藏输入，仅保存在本机）: ')


def write(path, content, private=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as stream:
        stream.write(content)
    if private:
        path.chmod(0o600)


def json_write(path, obj):
    write(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n', True)


def compose(*args, capture=False):
    command = ['docker', 'compose', '-f', str(ROOT / 'compose.yaml'),
               '--project-directory', str(ROOT), *args]
    if capture:
        return subprocess.run(command, check=True, text=True, encoding='utf-8',
                              errors='replace', capture_output=True)
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, encoding='utf-8', errors='replace')
    try:
        for line in process.stdout:
            print(line, end='')
        code = process.wait()
    except BaseException:
        process.terminate()
        process.wait()
        raise
    finally:
        process.stdout.close()
    if code:
        raise subprocess.CalledProcessError(code, command)
    return subprocess.CompletedProcess(command, code)


def preflight():
    if sys.version_info < (3, 9):
        raise ValueError('需要 Python 3.9+；Windows 建议 Python 3.12。')
    if not shutil.which('docker'):
        raise ValueError('未找到 Docker。Linux 先按 docs/INSTALL_LINUX.md 安装；Windows 先安装并启动 Docker Desktop。')
    compose('version')
    result = subprocess.run(['docker', 'info', '--format', '{{.OSType}}'],
                            check=True, capture_output=True, text=True)
    if result.stdout.strip() != 'linux':
        raise ValueError('需要 Linux 容器；请在 Docker Desktop 中切换到 Linux containers。')
    if not (ROOT / 'data/cmd_config.json').exists():
        for port in (6185, 6099):
            with socket.socket() as check:
                try:
                    check.bind(('127.0.0.1', port))
                except OSError:
                    raise ValueError(f'本机端口 {port} 被占用。请先按手册释放占用；不要重复创建第二套服务。') from None


def parse_ids(text):
    values = list(dict.fromkeys(re.split(r'[,，\s]+', text.strip()))) if text.strip() else []
    if any(not re.fullmatch(r'[1-9][0-9]{4,11}', value) for value in values):
        raise ValueError('QQ号和群号应为5到12位数字，可用逗号或空格分隔。')
    return values


def access_values(owner, users, groups):
    users = parse_ids(' '.join([owner, *users]))
    groups = parse_ids(' '.join(groups))
    return users, groups, [*[f'qq:FriendMessage:{u}' for u in users], *groups]


def init(root, owner, key, model='deepseek-flash', auto=True, base='https://api.deepseek.com/v1', users=(), groups=()):
    root = Path(root)
    config_path = root / 'data/cmd_config.json'
    if config_path.exists() or (root / 'napcat/config/onebot11.json').exists():
        raise ValueError('已有配置，初始化已停止；正常启停不会覆盖数据。')
    if not re.fullmatch(r'[1-9][0-9]{4,11}', owner):
        raise ValueError('主人QQ号应为5到12位数字（这里填你聊天的QQ，不是机器人QQ）。')
    if not key.strip() or key != key.strip() or '\n' in key or '\r' in key:
        raise ValueError('API Key 不能为空或包含换行、首尾空格。')
    allowed_users, allowed_groups, whitelist = access_values(owner, users, groups)
    token = secrets.token_hex(24)
    web_token = secrets.token_hex(24)
    password = 'DfY' + secrets.token_hex(12)
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 600000).hex()
    provider_id = f'deepseek/{model}'
    conf = {
        'config_version': 5,
        'platform': [{'id': 'qq', 'type': 'aiocqhttp', 'enable': True,
                      'ws_reverse_host': '0.0.0.0', 'ws_reverse_port': 6199, 'ws_reverse_token': token}],
        'provider_sources': [{'id': 'deepseek', 'provider': 'deepseek',
                              'type': 'openai_chat_completion', 'provider_type': 'chat_completion',
                              'enable': True, 'key': [key], 'api_base': base, 'timeout': 120,
                              'proxy': '', 'custom_headers': {}}],
        'provider': [{'id': provider_id, 'provider_source_id': 'deepseek',
                      'type': 'openai_chat_completion', 'provider_type': 'chat_completion',
                      'enable': True, 'model': model, 'modalities': ['text']}],
        'agent_runner': {'runner_type': 'local', 'config': {
            'model': {'provider_id': provider_id, 'request_max_retries': 1},
            'compression': {'max_turns': -1, 'overflow_strategy': 'llm_compress',
                            'fallback_max_tokens': 8000, 'keep_recent_ratio': 0.2,
                            'instruction': '用中文总结用户明确提及的个人资料、偏好、重要事件及未完成话题。不推测、不编造。'},
            'misc': {'max_steps': 3}}},
        'admins_id': [owner],
        'platform_settings': {'enable_id_white_list': True,
                              'id_whitelist': whitelist,
                              'unique_session': True,
                              'wl_ignore_admin_on_group': False,
                              'wl_ignore_admin_on_friend': True,
                              'friend_message_needs_wake_prefix': False,
                              'ignore_bot_self_message': True,
                              'segmented_reply': {'enable': True, 'interval': '1,2'}},
        'provider_settings': {'computer_use_runtime': 'none', 'web_search': False,
                              'proactive_capability': {'add_cron_tools': False}},
        'dashboard': {'username': 'astrbot', 'host': '0.0.0.0', 'port': 6185,
                      'password': hashlib.md5(password.encode()).hexdigest(),
                      'pbkdf2_password': f'pbkdf2_sha256$600000${salt}${hashed}',
                      'password_storage_upgraded': True, 'password_change_required': True},
        'disable_metrics': True, 'plugin_set': ['*'], 'timezone': 'Asia/Shanghai',
    }
    nap = {'network': {'httpServers': [], 'httpSseServers': [], 'httpClients': [],
                       'websocketServers': [], 'websocketClients': [{
                           'enable': True, 'name': 'dafeiyu', 'url': 'ws://astrbot:6199/ws',
                           'reportSelfMessage': False, 'messagePostFormat': 'array',
                           'token': token, 'debug': False, 'heartInterval': 30000,
                           'reconnectInterval': 5000}], 'plugins': []},
           'musicSignUrl': '', 'enableLocalFile2Url': False, 'parseMultMsg': False}
    for name in ['data/config', 'data/plugins', 'napcat/config', 'napcat/qq', 'napcat/plugins']:
        (root / name).mkdir(parents=True, exist_ok=True)
    if os.name != 'nt':
        for name in ['data', 'napcat']:
            (root / name).chmod(0o700)
    json_write(config_path, conf)
    json_write(root / 'napcat/config/onebot11.json', nap)
    json_write(root / 'napcat/config/webui.json', {'host': '0.0.0.0', 'port': 6099,
               'prefix': '', 'token': web_token, 'loginRate': 3})
    json_write(root / 'data/dafeiyu/settings.json', {'owner_qq': owner, 'auto_memory': auto,
               'allowed_users': allowed_users, 'allowed_groups': allowed_groups})
    shutil.copyfile(root / 'persona.txt', root / 'data/dafeiyu/persona.txt')
    shutil.copytree(root / 'plugins/astrbot_plugin_dafeiyu_memory',
                    root / 'data/plugins/astrbot_plugin_dafeiyu_memory',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    uid = os.getuid() if hasattr(os, 'getuid') else 1000
    gid = os.getgid() if hasattr(os, 'getgid') else 1000
    write(root / '.env', f'NAPCAT_UID={uid}\nNAPCAT_GID={gid}\n', True)
    write(root / 'credentials.txt', f'AstrBot 用户名: astrbot\n首次密码: {password}\nNapCat WebUI Token: {web_token}\n'
          '首次登录AstrBot后按提示改密码；此文件中旧密码不会自动更新。\n', True)
    (root / '.initialized').touch()


def initialized():
    if not (ROOT / 'data/cmd_config.json').exists():
        raise ValueError('请先运行 Linux 的 bash first-run.sh 或 Windows 的 setup.cmd 初始化。')


def wait_web():
    pending = {6185, 6099}
    for _ in range(60):
        for port in list(pending):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{port}/', timeout=1):
                    pending.remove(port)
            except urllib.error.HTTPError as exc:
                if exc.code < 500:
                    pending.remove(port)
            except (OSError, urllib.error.URLError):
                pass
        if not pending:
            return
        time.sleep(2)
    raise ValueError(f'容器已请求启动，但管理端口尚未就绪：{sorted(pending)}。运行 python3 manage.py logs 检查。')


def setup(args):
    preflight()
    if not (ROOT / 'data/cmd_config.json').exists():
        print('主人QQ号填平时与你的机器人聊天的那个QQ号；不是机器人登录号。')
        owner = input('主人QQ号: ').strip()
        key = hidden_key()
        model = input('模型 [deepseek-flash]: ').strip() or 'deepseek-flash'
        auto = input('每8条私聊自动整理长期记忆，会额外调用API [Y/n]: ').strip().lower() != 'n'
        users = parse_ids(input('其他允许私聊的QQ号（逗号分隔，可留空）: '))
        groups = parse_ids(input('允许聊天的QQ群号（逗号分隔，可留空，群内须@）: '))
        init(ROOT, owner, key, model, auto, users=users, groups=groups)
        print('已生成配置和随机密码；凭据在 credentials.txt。')
    else:
        print('检测到已有配置，继续使用，不重新初始化。')
    compose('config', '--quiet')
    if not args.no_pull:
        compose('pull')
    compose('up', '-d')
    wait_web()
    print('两个管理页面已响应。下一步：在 NapCat 扫码登录；仍需实际 QQ 收发验收。')
    print('同机浏览器直接打开下列地址；远程 Linux 访问方法见 docs/INSTALL_LINUX.md。')
    print('AstrBot: http://127.0.0.1:6185  NapCat: http://127.0.0.1:6099/webui')


def update_access(root, users, groups):
    root = Path(root)
    config_path = root / 'data/cmd_config.json'
    settings_path = root / 'data/dafeiyu/settings.json'
    conf = json.loads(config_path.read_text(encoding='utf-8-sig'))
    settings = json.loads(settings_path.read_text(encoding='utf-8-sig'))
    allowed_users, allowed_groups, whitelist = access_values(settings['owner_qq'], users, groups)
    conf['platform_settings'].update(enable_id_white_list=True, id_whitelist=whitelist,
                                    unique_session=True, wl_ignore_admin_on_group=False)
    settings.update(allowed_users=allowed_users, allowed_groups=allowed_groups)
    json_write(config_path, conf)
    json_write(settings_path, settings)
    shutil.copytree(root / 'plugins/astrbot_plugin_dafeiyu_memory',
                    root / 'data/plugins/astrbot_plugin_dafeiyu_memory', dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def access():
    initialized()
    print('主人仍是管理员。其他QQ只获得聊天权限，群内必须@；不同用户和群的记忆隔离。')
    users = parse_ids(input('允许私聊的其他QQ号（逗号分隔，主人自动保留）: '))
    groups = parse_ids(input('允许的QQ群号（逗号分隔，可留空）: '))
    compose('stop', 'astrbot')
    try:
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        for name in ['cmd_config.json', 'dafeiyu/settings.json']:
            source = ROOT / 'data' / name
            shutil.copyfile(source, source.with_name(source.name + '.before-access-' + stamp))
        update_access(ROOT, users, groups)
    finally:
        compose('start', 'astrbot')
    wait_web()
    print('聊天白名单已更新；主人管理员权限未扩展给其他人。')


def backup():
    initialized()
    folder = ROOT / 'backups'
    folder.mkdir(exist_ok=True)
    target = folder / ('dafeiyu-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f') + '.tar.gz')
    partial = target.with_suffix(target.suffix + '.partial')
    running = compose('ps', '--services', '--status', 'running', capture=True).stdout.split()
    compose('stop')  # consistent SQLite and QQ session snapshot
    try:
        with tarfile.open(partial, 'w:gz') as archive:
            for name in ['data', 'napcat', '.env', 'credentials.txt', '.initialized',
                         'compose.yaml', 'manage.py', 'setup.sh', 'install-docker.sh',
                         'first-run.sh', 'setup.cmd', 'manage.cmd', 'start.cmd', 'stop.cmd',
                         'setup.ps1', 'manage.ps1', 'persona.txt', 'plugins', 'docs', 'scripts',
                         'README.md', 'SOURCES.md', 'VALIDATION.md', 'VERSION', 'LICENSE']:
                path = ROOT / name
                if path.exists():
                    archive.add(path, arcname='aiassistrobot/' + name,
                                filter=lambda info: None if '__pycache__' in info.name else info)
        partial.chmod(0o600)
        partial.rename(target)
    finally:
        if running:
            compose('start', *running)
    print(f'备份完成：{target}\n包含记忆、对话、Key和QQ会话，请仅保存给自己。')


def doctor():
    initialized()
    compose('config', '--quiet')
    compose('ps')
    wait_web()
    conf = json.loads((ROOT / 'data/cmd_config.json').read_text(encoding='utf-8-sig'))
    source = conf['provider_sources'][0]
    request = urllib.request.Request(source['api_base'].rstrip('/') + '/models',
            headers={'Authorization': 'Bearer ' + source['key'][0]})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            models = [r['id'] for r in json.load(response)['data']]
        selected = conf['provider'][0]['model']
        print('API认证和模型列表通过。配置模型：', selected, '（列表可见）' if selected in models else '（不在返回列表中，请核对）')
        if selected not in models:
            return 1
    except Exception as exc:
        print('API模型列表检查未通过：', type(exc).__name__)
        return 1
    print('管理页和API检查通过；这不代表QQ已登录或已成功收发。请按README做实际聊天与重启测试。')
    return 0


def main():
    if os.name != 'nt':
        os.umask(0o077)
    parser = argparse.ArgumentParser(description='大肥鱼 QQ：Linux / Windows 部署管理')
    parser.add_argument('action', choices=['setup', 'access', 'start', 'stop', 'restart', 'status', 'logs', 'backup', 'doctor'])
    parser.add_argument('--no-pull', action='store_true', help='已导入离线镜像时跳过拉取')
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.action == 'setup':
        return first_run(args)
    elif args.action == 'access':
        access()
    elif args.action == 'backup':
        backup()
    elif args.action == 'doctor':
        return doctor()
    else:
        initialized()
        commands = {'start': ['up', '-d'], 'stop': ['stop'], 'restart': ['restart'],
                    'status': ['ps'], 'logs': ['logs', '--tail', '100', '-f']}
        compose(*commands[args.action])
        if args.action in ['start', 'restart']:
            wait_web()
            print('管理页已响应；QQ状态请到NapCat查看。')
    return 0


def first_run(args):
    folder = ROOT / 'logs'
    folder.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    logfile = folder / f'first-run-{stamp}.log'
    status = folder / 'first-run.status'
    write(logfile, '', True)
    write(status, f'RUNNING {stamp}\n', True)
    out, err = sys.stdout, sys.stderr
    with logfile.open('a', encoding='utf-8') as log:
        sys.stdout, sys.stderr = Tee(out, log), Tee(err, log)
        code = 1
        try:
            print(f'大肥鱼 QQ {VERSION} | {datetime.datetime.now().astimezone().isoformat()}')
            print(f'部署目录：{ROOT}\n首次日志：{logfile}')
            print('Key 隐藏输入；日志和容器日志仅留给自己，不要上传到 GitHub。')
            setup(args)
            code = doctor()
            write(status, f'{"READY_AWAITING_QQ_LOGIN" if code == 0 else "API_CHECK_FAILED"} {stamp}\n', True)
            return code
        except BaseException as exc:
            print(f'配置或启动失败：{type(exc).__name__}: {exc}', file=sys.stderr)
            write(status, f'FAILED {stamp}\n', True)
            raise
        finally:
            try:
                result = compose('logs', '--no-color', '--timestamps', '--tail', '100', capture=True)
                write(folder / f'containers-first-{stamp}.log', result.stdout, True)
            except (OSError, subprocess.CalledProcessError):
                pass
            print(f'运行状态：{status.read_text(encoding="utf-8").strip()}\n日志已保存：{logfile}')
            sys.stdout, sys.stderr = out, err


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError, getpass.GetPassWarning) as exc:
        print('操作未完成：', exc, file=sys.stderr)
        sys.exit(1)
