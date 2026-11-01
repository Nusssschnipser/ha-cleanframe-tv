"""Translate Supervisor options into the existing bridge configuration."""
import json
from pathlib import Path
import sys
from bridge.server import DEFAULT_APPS, validate_config, main as bridge_main


def make_config(options):
    apps = dict(DEFAULT_APPS)
    for item in options.get('additional_apps', []):
        if not isinstance(item, dict) or set(item) != {'app_id', 'name'}:
            raise ValueError('Each additional app needs app_id and name')
        apps[item['app_id']] = item['name']
    return validate_config({
        'tv': options['tv_host'], 'host': options['ha_host'],
        'listen': options['ha_host'], 'port': options.get('port', 8767),
        'allow_clients': [options['ha_host']],
        'sdb': '/usr/local/bin/sdb', 'apps': apps,
    })


def main():
    try:
        options = json.loads(Path('/data/options.json').read_text())
        config = make_config(options)
    except (OSError, ValueError, KeyError, TypeError) as err:
        raise SystemExit('Configure valid tv_host and ha_host IPv4 addresses, port and app entries in the app options.') from err
    path = Path('/data/bridge.json')
    path.write_text(json.dumps(config))
    path.chmod(0o600)
    sys.argv = ['bridge', '--config', str(path)]
    bridge_main()

if __name__ == '__main__': main()
