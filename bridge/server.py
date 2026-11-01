"""Run from repository root: python3 -m bridge.server --config .local/bridge.json."""
import argparse
import hashlib
import ipaddress
import json
from pathlib import Path
import re
import subprocess
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from transport import capture  # Reuses the previously documented SDB callback path.

APP_PATTERN = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}')
DEFAULT_APPS = {
    'nClrkHome1.FrameHome': 'CleanFrame',
    'org.cleanframe.samsung-home': 'Samsung Home',
    'org.tizen.tv-viewer': 'Fernsehen',
    'SrAoJxGQUf.ARD': 'ARD Mediathek',
    'yPSlpvfeTf.ZDFmediathek': 'ZDF',
}

class BridgeError(Exception):
    """A safe, user-facing bridge failure."""


def validate_config(config):
    result = dict(config)
    for field in ('tv', 'host', 'listen'):
        addr = ipaddress.IPv4Address(result[field])
        if addr.is_unspecified or addr.is_multicast:
            raise ValueError('Use a specific unicast address for ' + field)
        result[field] = str(addr)
    if result['listen'] not in (result['host'], '127.0.0.1'):
        raise ValueError('Listen must be the callback host or loopback')
    if not isinstance(result.get('port'), int) or not 1024 <= result['port'] <= 65535:
        raise ValueError('Invalid bridge port')
    result['allow_clients'] = [str(ipaddress.IPv4Address(a)) for a in result['allow_clients']]
    if not result['allow_clients'] or any(ipaddress.ip_address(a).is_unspecified or ipaddress.ip_address(a).is_multicast for a in result['allow_clients']):
        raise ValueError('Explicit client addresses required')
    sdb = Path(result['sdb'])
    if not sdb.is_absolute() or not sdb.is_file():
        raise ValueError('SDB must be an existing absolute file path')
    apps = result.get('apps', DEFAULT_APPS)
    if not isinstance(apps, dict) or not apps or len(apps) > 100:
        raise ValueError('Expected 1-100 allowed apps')
    for app, name in apps.items():
        if not APP_PATTERN.fullmatch(app) or not isinstance(name, str) or not 1 <= len(name) <= 100:
            raise ValueError('Invalid app catalog')
    result['apps'] = dict(apps)
    return result


class Controller:
    def __init__(self, config):
        self.config = validate_config(config)
        self.lock = threading.Lock()
        self.staged = None
        self.results = {}  # Request IDs are never automatically retried after uncertainty.

    def status(self):
        online = compatible = False
        try:
            # Bypass environment proxies: the TV is always a literal local address.
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open('http://' + self.config['tv'] + ':8001/api/v2/', timeout=3) as r:
                data = json.loads(r.read(65536))
            if not isinstance(data, dict) or not isinstance(data.get('device'), dict):
                raise ValueError('Invalid TV status')
            device = data['device']
            online = device.get('PowerState') == 'on'
            compatible = device.get('modelName') == 'GQ65Q95TDTXZG'
        except (OSError, ValueError, TypeError):
            pass
        return {'api_version': 1, 'online': online, 'compatible': compatible,
                'apps': self.config['apps'], 'model': 'GQ65Q95TDTXZG'}

    def sdb(self, *args):
        try:
            result = subprocess.run([self.config['sdb'], *args], capture_output=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as err:
            raise BridgeError('SDB unavailable or timed out; check developer access') from err
        if result.returncode:
            raise BridgeError('SDB command failed; check developer access')

    def stage(self):
        files = [ROOT / 'native-launcher' / 'out' / ('Q95Launch' + suffix)
                 for suffix in ('.dll', '.deps.json', '.runtimeconfig.json')]
        if any(not p.is_file() for p in files):
            raise BridgeError('Build native-launcher/Launcher.csproj first')
        digest = hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()[:12]
        self.sdb('connect', self.config['tv'] + ':26101')
        remote = '/home/owner/share/tmp/sdk_tools/cf-ha-' + digest
        # Use a versioned directory: partial or concurrent updates cannot mix helpers.
        if self.staged != remote:
            output = capture(self.config, 'mkdir -p ' + remote + ' && echo CF_DIR_READY', 'ha-stage')
            if 'CF_DIR_READY' not in output:
                raise BridgeError('Cannot prepare launcher directory')
            for file in files:
                self.sdb('-s', self.config['tv'] + ':26101', 'push', str(file), remote + '/' + file.name)
            self.staged = remote
        return remote

    def execute(self, data):
        if not isinstance(data, dict) or set(data) - {'action', 'app_id', 'request_id'}:
            raise ValueError('Invalid request')
        request_id = data.get('request_id', '')
        if not isinstance(request_id, str) or not re.fullmatch('[a-f0-9]{32}', request_id):
            raise ValueError('A 32-character hex request_id is required')
        action, app = data.get('action'), data.get('app_id')
        if action == 'launch_app':
            if not isinstance(app, str) or app not in self.config['apps']:
                raise ValueError('App is not in the configured allowlist')
            mode = 'app'
        elif action == 'tv_settings' and app is None:
            app, mode = 'org.tizen.menu', 'settings'
        else:
            raise ValueError('Unknown action')
        if not self.lock.acquire(blocking=False):
            raise BridgeError('TV command already in progress')
        try:
            if request_id in self.results:
                raise BridgeError('Request already submitted; do not repeat an uncertain command')
            status = self.status()
            if not status['online'] or not status['compatible']:
                raise BridgeError('TV is off, unreachable or not the supported model')
            remote = self.stage()
            if len(self.results) >= 10000:
                raise BridgeError('Request limit reached; restart bridge after reviewing logs')
            self.results[request_id] = 'submitted'
            command = (f'unset AUL_APPID\n/usr/bin/dotnet-launcher {remote}/Q95Launch.dll {request_id} {mode} {app} 3>&-\n'
                       f'echo LAUNCHER_RC:$?\ncat /home/owner/share/tmp/sdk_tools/cf-ha-result-{request_id}.txt')
            # Keep transport <=400 bytes: stage a short, uniquely named invocation.
            local = ROOT / '.local' / ('ha-' + request_id + '.sh')
            local.parent.mkdir(exist_ok=True)
            local.write_text(command + '\n')
            script = '/home/owner/share/tmp/sdk_tools/ha-' + request_id + '.sh'
            self.sdb('-s', self.config['tv'] + ':26101', 'push', str(local), script)
            try:
                output = capture(self.config, 'cat ' + script + '|bash', 'ha-launch', timeout=15)
            except Exception as err:
                self.staged = None
                raise BridgeError('No complete TV acknowledgement; execution state unknown, no automatic retry') from err
            finally:
                local.unlink(missing_ok=True)
            if 'CF_LAUNCH_ACCEPTED' not in output.splitlines() or not re.search(r'^LAUNCHER_RC:0$', output, re.M):
                raise BridgeError('TV rejected the launch or request was already executed; check local evidence')
            self.results[request_id] = 'accepted'
            return {'accepted': True, 'request_id': request_id, 'display_verified': False}
        finally:
            self.lock.release()


def make_handler(controller):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def log_message(self, *_args):
            pass  # No addresses, request parameters or tokens in access logs.

        def respond(self, code, data):
            body = json.dumps(data).encode()
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def permitted(self):
            if self.client_address[0] not in controller.config['allow_clients'] or self.headers.get('Origin'):
                self.respond(403, {'error': 'Client not allowed'})
                return False
            return True

        def do_GET(self):
            if not self.permitted(): return
            if self.path != '/v1/status':
                self.respond(404, {'error': 'Not found'}); return
            self.respond(200, controller.status())

        def do_POST(self):
            if not self.permitted(): return
            if self.path != '/v1/action':
                self.respond(404, {'error': 'Not found'}); return
            try:
                if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                    raise ValueError('JSON required')
                length = int(self.headers.get('Content-Length', '0'))
                if not 1 <= length <= 4096 or self.headers.get('Transfer-Encoding'):
                    raise ValueError('Invalid body length')
                data = json.loads(self.rfile.read(length))
                result = controller.execute(data)
            except (ValueError, TypeError):
                self.respond(400, {'error': 'Invalid action, app or request ID'}); return
            except BridgeError as err:
                self.respond(503, {'error': str(err)}); return
            except Exception:
                self.respond(500, {'error': 'Bridge failure; execution state unknown, no automatic retry'}); return
            self.respond(200, result)
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    controller = Controller(json.loads(Path(args.config).read_text()))
    server = ThreadingHTTPServer((controller.config['listen'], controller.config['port']), make_handler(controller))
    server.daemon_threads = True
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()

if __name__ == '__main__': main()
