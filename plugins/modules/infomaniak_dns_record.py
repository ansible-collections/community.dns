#!/usr/bin/python
# Copyright (c) 2026 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: infomaniak_dns_record

short_description: Add or delete a single record in Infomaniak DNS service

version_added: 4.1.0

description:
  - Creates and deletes single DNS records in Infomaniak DNS service.
  - If you do not want to add/remove values, but replace values, you will be interested in modifying a B(record set) and not
    a single record. This is in particular important when working with C(CNAME) and C(SOA) records. Use the M(community.dns.infomaniak_dns_record_set)
    module for working with record sets.
extends_documentation_fragment:
  - community.dns._infomaniak
  - community.dns._infomaniak.record_default_ttl
  - community.dns._infomaniak.record_notes
  - community.dns._infomaniak.record_type_choices
  - community.dns._infomaniak.record_type_seealso
  - community.dns._module_record
  - community.dns._options.record_transformation
  - community.dns._attributes
  - community.dns._attributes.actiongroup_infomaniak
  - community.dns._zone_name_id.name_only_modify

author:
  - Felix Fontein (@felixfontein)
"""

EXAMPLES = r"""
- name: Add a new.foo.com A record
  community.dns.infomaniak_dns_record:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value: 1.1.1.1
    infomaniak_token: access_token

- name: Add A record using prefix for www.example.com
  community.dns.infomaniak_dns_record:
    state: present
    zone_name: example.com
    prefix: www
    type: A
    value: 198.51.100.25
    infomaniak_token: "{{ lookup('env', 'INFOMANIAK_DNS_TOKEN') }}"

- name: Remove a new.foo.com A record
  community.dns.infomaniak_dns_record:
    state: absent
    zone_name: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value: 2.2.2.2
    infomaniak_token: access_token
"""

RETURN = r"""
zone_id:
  description: The ID of the zone.
  type: str
  returned: success
  sample: foo.com
"""

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils._argspec import (
    ModuleOptionProvider,
)
from ansible_collections.community.dns.plugins.module_utils._http import (
    ModuleHTTPHelper,
)
from ansible_collections.community.dns.plugins.module_utils._infomaniak.api import (
    create_infomaniak_api,
    create_infomaniak_argument_spec,
    create_infomaniak_provider_information,
)
from ansible_collections.community.dns.plugins.module_utils._module.record import (
    create_module_argument_spec,
    run_module,
)


def main() -> None:
    provider_information = create_infomaniak_provider_information()
    argument_spec = create_infomaniak_argument_spec()
    argument_spec.merge(
        create_module_argument_spec(provider_information=provider_information)
    )
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    option_provider = ModuleOptionProvider(module)
    run_module(
        module,
        lambda: create_infomaniak_api(option_provider, ModuleHTTPHelper(module)),
        provider_information=create_infomaniak_provider_information(
            option_provider=option_provider
        ),
    )


if __name__ == "__main__":
    main()
