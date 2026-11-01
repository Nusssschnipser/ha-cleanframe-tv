"""Keep the app build context reproducible; --check verifies committed sources."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
FILES = ['bridge/__init__.py', 'bridge/server.py', 'scripts/config.py', 'scripts/transport.py',
         'native-launcher/Launcher.csproj', 'native-launcher/Program.cs']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    dest = ROOT / 'cleanframe_tv_bridge/rootfs/app'
    for name in FILES:
        src, target = ROOT / name, dest / name
        if args.check:
            if not target.is_file() or target.read_bytes() != src.read_bytes():
                raise SystemExit('Stale app build source: ' + name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, target)
    print('App build sources match canonical sources.')

if __name__ == '__main__': main()
