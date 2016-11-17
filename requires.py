from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


class NeutronPluginRequires(RelationBase):
    scope = scopes.GLOBAL

    @hook('{requires:neutron-plugin}-relation-{joined,changed}')
    def changed(self):
        self.set_state('{relation_name}.connected')

    @hook('{requires:neutron-plugin}-relation-{broken,departed}')
    def broken(self):
        self.remove_state('{relation_name}.connected')
