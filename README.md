# Overview

This interface provides the reactive interface for the neutron-plugin relation.
This is used by the neutron-openvswitch subordinate amongst others.

# metadata

To consume this interface in your charm or layer, add the following to
`layer.yaml`:

```yaml
includes: ['interface:neutron-plugin']
```

and add a provides interface of type `<name>` to your charm or layers
`metadata.yaml`:

```yaml
provides:
  <name>:
    interface: neutron-plugin
    scope: container
```

where `name` is what you want to refer to the interface in the principal charm.

# Bugs

Please report bugs on
[Launchpad](https://bugs.launchpad.net/openstack-charms/+filebug).

For development questions please refer to the OpenStack
[Charm Guide](https://github.com/openstack/charm-guide).
