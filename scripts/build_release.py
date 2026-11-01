"""Build allowlisted online installers without user data or credentials (stdlib)."""
import argparse
import gzip
import hashlib
import io
from pathlib import Path
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
COMMON = ['VERSION', 'LICENSE', 'README.md', 'SOURCES.md', 'VALIDATION.md', 'compose.yaml',
          'manage.py', 'persona.txt', '.gitignore', '.gitattributes']
LINUX = ['setup.sh', 'first-run.sh', 'install-docker.sh']
WINDOWS = ['setup.cmd', 'manage.cmd', 'start.cmd', 'stop.cmd', 'setup.ps1', 'manage.ps1']


def release_files(root, platform):
    names = set(COMMON + LINUX + WINDOWS)  # Backups remain portable across platforms.
    for folder in ('docs', 'plugins'):
        names.update(p.relative_to(root).as_posix() for p in (root / folder).rglob('*')
                     if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')
    # Runtime data and credentials are never selected by this allowlist.
    for name in sorted(names):
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f'Not a regular release source file: {name}')
        yield name, path


def content(path):
    data = path.read_bytes().replace(b'\r\n', b'\n')
    if path.suffix in ('.cmd', '.ps1'):
        data = data.replace(b'\n', b'\r\n')
    return data


def build(root=ROOT, destination=None):
    destination = Path(destination or root / 'dist')
    destination.mkdir(parents=True, exist_ok=True)
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    linux = destination / f'aiassistrobot-qq-{version}-linux.tar.gz'
    windows = destination / f'aiassistrobot-qq-{version}-windows.zip'
    for platform, target in [('linux', linux), ('windows', windows)]:
        top = f'aiassistrobot-{platform}'
        if platform == 'linux':
            with target.open('wb') as output:
                with gzip.GzipFile(filename='', mode='wb', fileobj=output, mtime=0) as zipped:
                    with tarfile.open(fileobj=zipped, mode='w') as archive:
                        for name, path in release_files(root, platform):
                            data = content(path)
                            info = tarfile.TarInfo(f'{top}/{name}')
                            info.size = len(data)
                            info.mode = 0o755 if path.suffix == '.sh' else 0o644
                            info.mtime = 0
                            archive.addfile(info, io.BytesIO(data))
        else:
            with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
                for name, path in release_files(root, platform):
                    info = zipfile.ZipInfo(f'{top}/{name}', date_time=(2026, 11, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    archive.writestr(info, content(path))
    sums = ''.join(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n' for p in (linux, windows))
    (destination / 'SHA256SUMS.txt').write_text(sums, encoding='ascii')
    print(sums, end='')
    return linux, windows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    build(destination=parser.parse_args().out)
