"""App option validation without Supervisor or device access."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('addon_run', ROOT / 'cleanframe_tv_bridge/run.py')
addon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)

class AppTests(unittest.TestCase):
    def test_host_owns_bridge_and_client_allowlist(self):
        with patch('pathlib.Path.is_file', return_value=True):
            config = addon.make_config({'tv_host': '192.0.2.10', 'ha_host': '192.0.2.20', 'port': 8767})
        self.assertEqual(config['host'], '192.0.2.20')
        self.assertEqual(config['listen'], config['host'])
        self.assertEqual(config['allow_clients'], [config['host']])
        self.assertNotIn('token', config)
        self.assertEqual(len(config['apps']), 5)

    def test_additional_apps_keep_defaults(self):
        with patch('pathlib.Path.is_file', return_value=True):
            config = addon.make_config({'tv_host': '192.0.2.10', 'ha_host': '192.0.2.20',
                                       'additional_apps': [{'app_id': 'Example.App', 'name': 'Example'}]})
        self.assertIn('nClrkHome1.FrameHome', config['apps'])
        self.assertEqual(config['apps']['Example.App'], 'Example')

    def test_invalid_app_or_blank_host_rejected(self):
        with patch('pathlib.Path.is_file', return_value=True):
            with self.assertRaises(ValueError):
                addon.make_config({'tv_host': '192.0.2.10', 'ha_host': ''})
            with self.assertRaises(ValueError):
                addon.make_config({'tv_host': '192.0.2.10', 'ha_host': '192.0.2.20',
                                  'additional_apps': [{'app_id': 'x;reboot', 'name': 'bad'}]})

if __name__ == '__main__': unittest.main()
