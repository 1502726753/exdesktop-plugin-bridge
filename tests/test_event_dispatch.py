"""Check Python host dispatch only; this does not test the native C++ bridge."""
import os
import sys
import types
import unittest
from pathlib import Path

upstream = Path(os.environ['EXDESKTOP_SOURCE'])
sys.path.insert(0, str(upstream / 'Telegram/SourceFiles/extera/python'))
sys.modules['_extera'] = types.ModuleType('_extera')
import extera_host as host
import base_plugin


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.saved = host._records
        host._records = {}

    def tearDown(self):
        host._records = self.saved

    def test_update_is_delivered_to_plugin(self):
        observed = []
        class Listener(base_plugin.BasePlugin):
            def on_update_hook(self, name, account, update):
                observed.append((name, account, update.copy()))
        host._records['listener'] = types.SimpleNamespace(id='listener', instance=Listener())
        payload = {'id': 12, 'dialog_id': 34, 'out': False, 'date': 123, 'sender_id': 56, 'text': 'example'}
        self.assertTrue(host._event({'type': 'update', 'name': 'updateDeletedMessage', 'account': 0, 'update': payload}))
        self.assertEqual(observed, [('updateDeletedMessage', 0, payload)])

    def test_one_plugin_failure_does_not_stop_other_plugins(self):
        observed = []
        class Failing(base_plugin.BasePlugin):
            def on_update_hook(self, name, account, update):
                raise RuntimeError('test failure')
        class Listener(base_plugin.BasePlugin):
            def on_update_hook(self, name, account, update):
                observed.append(name)
        host._records['bad'] = types.SimpleNamespace(id='bad', instance=Failing())
        host._records['good'] = types.SimpleNamespace(id='good', instance=Listener())
        host._event({'type': 'update', 'name': 'updateDeletedMessage', 'account': 0, 'update': {'id': 1}})
        self.assertEqual(observed, ['updateDeletedMessage'])

if __name__ == '__main__':
    unittest.main()
