import json
import os
import uuid

from charms.reactive import hook
from charms.reactive import RelationBase
from charms.reactive import scopes


METADATA_KEY = 'metadata-shared-secret'
LEGACY_SECRET_FILE = "/etc/neutron/secret.txt"


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

    def get_or_create_shared_secret(self):
        """Retrieves a shared secret from local unit storage.

        The secret is created if it does not already exist.

        :returns: Shared secret
        :rtype: str
        """
        secret = self.get_local(METADATA_KEY)
        if secret is None:
            # If the secrets file is present then reuse the secret to ensure
            # compatability with the existing setup.
            if os.path.exists(LEGACY_SECRET_FILE):
                with open(LEGACY_SECRET_FILE, 'r') as secret_file:
                    secret = secret_file.read().strip()
            else:
                secret = str(uuid.uuid4())
            self.set_local(METADATA_KEY, secret)
        return secret

    def publish_shared_secret(self):
        """Publish the shared secret on the relation."""
        conversation = self.conversation()
        relation_info = {
            METADATA_KEY: self.get_or_create_shared_secret(),
        }
        conversation.set_remote(**relation_info)
