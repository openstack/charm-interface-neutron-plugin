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
import json
import mock

import charms_openstack.test_utils as test_utils

import provides


_hook_args = {}


def mock_hook(*args, **kwargs):

    def inner(f):
        # remember what we were passed.  Note that we can't actually determine
        # the class we're attached to, as the decorator only gets the function.
        _hook_args[f.__name__] = dict(args=args, kwargs=kwargs)
        return f
    return inner


class TestNeutronPluginProvides(test_utils.PatchHelper):

    @classmethod
    def setUpClass(cls):
        cls._patched_hook = mock.patch('charms.reactive.hook', mock_hook)
        cls._patched_hook_started = cls._patched_hook.start()
        # force providesto rerun the mock_hook decorator:
        # try except is Python2/Python3 compatibility as Python3 has moved
        # reload to importlib.
        try:
            reload(provides)
        except NameError:
            import importlib
            importlib.reload(provides)

    @classmethod
    def tearDownClass(cls):
        cls._patched_hook.stop()
        cls._patched_hook_started = None
        cls._patched_hook = None
        # and fix any breakage we did to the module
        try:
            reload(provides)
        except NameError:
            import importlib
            importlib.reload(provides)

    def setUp(self):
        self._patches = {}
        self._patches_start = {}
        conversation = mock.MagicMock()
        self.target = provides.NeutronPluginProvides(
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
                '{provides:neutron-plugin}-'
                'relation-{joined,changed}', ),
            'broken': (
                '{provides:neutron-plugin}-'
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

    def test_configure_plugin(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('set_remote')
        self.target.configure_plugin('aPlugin',
                                     {'aKey': 'aValue'},
                                     )
        conversation.set_remote.assert_called_once_with(
            **{
                'neutron-plugin': 'aPlugin',
                'subordinate_configuration': json.dumps({'aKey': 'aValue'})},
        )

    def test_get_or_create_shared_secret(self):
        self.patch_target('get_local')
        self.get_local.return_value = None
        self.patch_target('set_local')
        self.patch_object(provides.uuid, 'uuid4')
        self.uuid4.return_value = 'fake-uuid'
        self.assertEquals(
            self.target.get_or_create_shared_secret(), 'fake-uuid')
        self.set_local.assert_called_once_with(
            provides.METADATA_KEY, 'fake-uuid')

    def test_publish_shared_secret(self):
        conversation = mock.MagicMock()
        self.patch_target('conversation', conversation)
        self.patch_target('get_or_create_shared_secret')
        self.get_or_create_shared_secret.return_value = 'fake-uuid'
        self.target.publish_shared_secret()
        conversation.set_remote.assert_called_once_with(
            **{provides.METADATA_KEY: 'fake-uuid'})
