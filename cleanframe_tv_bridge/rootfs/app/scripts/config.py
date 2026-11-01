"""Local configuration; importing this module never contacts a device."""
import ipaddress
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local'
MODEL = 'GQ65Q95TDTXZG'
FIRMWARE = 'T-NKMDEUC-2743.0'


def load(path=None):
    data = json.loads(Path(path or LOCAL / 'config.json').read_text())
    for name in ('tv', 'host'):
        address = ipaddress.IPv4Address(data[name])
        if address.is_unspecified or address.is_multicast or address.is_loopback:
            raise ValueError('Use an actual TV/host LAN IPv4 address')
        data[name] = str(address)
    sdk = Path(data['sdb']).expanduser()
    if not sdk.is_absolute() or not sdk.is_file():
        raise ValueError('sdb must point to an existing absolute SDK executable')
    data['sdb'] = str(sdk)
    return data


def validate_baseline(data, tv):
    expected = {'tv': tv, 'model': MODEL, 'firmware': FIRMWARE,
                'home_alias': None, 'escape_alias': None, 'autostart': 0}
    if any(k not in data or data[k] != v for k, v in expected.items()):
        raise ValueError('Saved original state does not match this controller/TV')
    return data
