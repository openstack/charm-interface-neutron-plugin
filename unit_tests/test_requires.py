# Copyright 2019 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import mock

import charms_openstack.test_utils as test_utils

import requires


_hook_args = {}


def mock_hook(*args, **kwargs):

    def inner(f):
        # remember what we were passed.  Note that we can't actually determine
        # the class we're attached to, as the decorator only gets the function.
        _hook_args[f.__name__] = dict(args=args, kwargs=kwargs)
        return f
    return inner


class TestNeutronPluginRequires(test_utils.PatchHelper):

    @classmethod
    def setUpClass(cls):
        cls._patched_hook = mock.patch('charms.reactive.hook', mock_hook)
        cls._patched_hook_started = cls._patched_hook.start()
        # force requires to rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    @classmethod
    def tearDownClass(cls):
        cls._patched_hook.stop()
        cls._patched_hook_started = None
        cls._patched_hook = None
        # and fix any breakage we did to the module
        try:
            reload(requires)
        except NameError:
            import importlib
            importlib.reload(requires)

    def setUp(self):
        self._patches = {}
        self._patches_start = {}
        conversation = mock.MagicMock()
        self.target = requires.NeutronPluginRequires(
            'some-relation', [conversation])

    def tearDown(self):
        self.target = None
        for k, v in self._patches.items():
            v.stop()
            setattr(self, k, None)
        self._patches = None
        self._patches_start = None

    def patch_target(self, attr, return_value=None):
        mocked = mock.patch.object(self.target, attr)
        self._patches[attr] = mocked
        started = mocked.start()
        started.return_value = return_value
        self._patches_start[attr] = started
        setattr(self, attr, started)

    def patch_topublish(self):
        self.patch_target('_relations')
        relation = mock.MagicMock()
        to_publish = mock.PropertyMock()
        type(relation).to_publish = to_publish
        self._relations.__iter__.return_value = [relation]
        return relation.to_publish

    def test_registered_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_patterns = {
            'changed': (
                '{requires:neutron-plugin}-'
                'relation-{joined,changed}', ),
            'broken': (
                '{requires:neutron-plugin}-'
                'relation-{broken,departed}', ),
        }
        for k, v in _hook_args.items():
            self.assertEqual(hook_patterns[k], v['args'])

    def test_changed(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('set_state')
        self.target.changed()
        self.set_state.assert_has_calls([
            mock.call('{relation_name}.connected'),
        ])

    def test_broken(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('remove_state')
        self.target.broken()
        self.remove_state.assert_has_calls([
            mock.call('{relation_name}.connected'),
        ])

    def test_host(self):
        conversation = mock.MagicMock()
        conversation.get_remote.return_value = 'someHost.fqdn'
        self.patch_target('conversation', conversation)
        self.assertEquals(self.target.host(), 'someHost.fqdn')
