import json

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class NeutronPluginProvides(RelationBase):
    scope = scopes.GLOBAL

    @hook('{provides:neutron-plugin}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')

    @hook('{provides:neutron-plugin}-relation-{broken,departed}')
    def broken(self):
        self.remove_state('{relation_name}.connected')

    def configure_plugin(self, plugin, config):
        conversation = self.conversation()
        relation_info = {
            'neutron-plugin': plugin,
            'subordinate_configuration': json.dumps(config),
        }
        conversation.set_remote(**relation_info)
