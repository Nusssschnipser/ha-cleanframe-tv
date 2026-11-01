"""Offline bridge tests: no TV or real SDB is used."""
from pathlib import Path
import sys
import base64
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bridge.server import Controller, BridgeError, make_handler, validate_config
from http.server import ThreadingHTTPServer

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        sdb = self.root / 'sdb'
        sdb.touch()
        self.config = {'tv': '192.0.2.10', 'host': '192.0.2.20', 'listen': '127.0.0.1',
                       'sdb': str(sdb), 'port': 8767, 'allow_clients': ['127.0.0.1']}
        self.controller = Controller(self.config)
        self.request = {'action': 'launch_app', 'app_id': 'nClrkHome1.FrameHome', 'request_id': 'a' * 32}

    def test_reject_wildcard_listener_and_untrusted_apps(self):
        with self.assertRaises(ValueError): validate_config(dict(self.config, listen='0.0.0.0'))
        with self.assertRaises(ValueError): validate_config(dict(self.config, apps={'bad;id': 'bad'}))
        with self.assertRaises(ValueError): self.controller.execute(dict(self.request, app_id='x;reboot'))
        with self.assertRaises(ValueError): self.controller.execute(dict(self.request, request_id='../x'))
        with self.assertRaises(ValueError): self.controller.execute(dict(self.request, command='id'))

    def test_offline_stages_nothing(self):
        with patch.object(self.controller, 'status', return_value={'online': False, 'compatible': True}), patch.object(self.controller, 'stage') as stage:
            with self.assertRaises(BridgeError): self.controller.execute(self.request)
            stage.assert_not_called()

    def test_settings_sequence_and_repeated_request(self):
        captured = []
        def sdb(*args):
            if 'push' in args:
                captured.append(Path(args[-2]).read_text())
        with patch('bridge.server.ROOT', self.root), patch.object(self.controller, 'status', return_value={'online': True, 'compatible': True}), patch.object(self.controller, 'stage', return_value='/sdk/helper'), patch.object(self.controller, 'sdb', side_effect=sdb), patch('bridge.server.capture', return_value='LAUNCHER_RC:0\nCF_LAUNCH_ACCEPTED\n') as capture:
            result = self.controller.execute({'action': 'tv_settings', 'request_id': 'b' * 32})
            self.assertTrue(result['accepted'])
            self.assertFalse(result['display_verified'])
            self.assertIn('settings org.tizen.menu', captured[0])
            with self.assertRaises(BridgeError): self.controller.execute({'action': 'tv_settings', 'request_id': 'b' * 32})
            self.assertEqual(capture.call_count, 1)

    def test_timeout_never_retries(self):
        with patch('bridge.server.ROOT', self.root), patch.object(self.controller, 'status', return_value={'online': True, 'compatible': True}), patch.object(self.controller, 'stage', return_value='/sdk/helper'), patch.object(self.controller, 'sdb'), patch('bridge.server.capture', side_effect=TimeoutError) as capture:
            with self.assertRaisesRegex(BridgeError, 'unknown'): self.controller.execute(self.request)
            with self.assertRaises(BridgeError): self.controller.execute(self.request)
            self.assertEqual(capture.call_count, 1)

    def test_status_handles_malformed_or_offline_tv(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=OSError):
            self.assertFalse(self.controller.status()['online'])

    def test_partial_ack_is_not_success(self):
        with patch('bridge.server.ROOT', self.root), patch.object(self.controller, 'status', return_value={'online': True, 'compatible': True}), patch.object(self.controller, 'stage', return_value='/sdk/helper'), patch.object(self.controller, 'sdb'), patch('bridge.server.capture', return_value='CF_LAUNCH_ACCEPTED\nLAUNCHER_RC:3\n'):
            with self.assertRaises(BridgeError): self.controller.execute(self.request)

    def test_http_origin_and_client_rejected(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(self.controller))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/v1/status'
            req = urllib.request.Request(url, headers={'Origin': 'https://example.org'})
            with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(req)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            self.controller.config['allow_clients'] = ['192.0.2.30']
            with self.assertRaises(urllib.error.HTTPError) as error: urllib.request.urlopen(url)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_callback_argument_stays_bounded(self):
        from transport import build_argument
        arg = build_argument('cat /home/owner/share/tmp/sdk_tools/ha-' + 'a' * 32 + '.sh|bash', '192.0.2.20', 65000, 'a' * 12)
        self.assertLessEqual(len(arg.encode()), 400)
        encoded = arg.split('printf${IFS}%s${IFS}', 1)[1].split('|', 1)[0]
        payload = base64.b64decode(encoded)
        checked = subprocess.run(['bash', '-n'], input=payload, capture_output=True)
        self.assertEqual(checked.returncode, 0, checked.stderr.decode())

if __name__ == '__main__': unittest.main()
