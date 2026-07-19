#!/usr/bin/python
# Copyright (c) 2026 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: infomaniak_dns_record_sets

short_description: Bulk synchronize DNS record sets in Infomaniak DNS service

version_added: 4.1.0

description:
  - Bulk synchronize DNS record sets in Infomaniak DNS service.
extends_documentation_fragment:
  - community.dns._infomaniak
  - community.dns._infomaniak.record_notes
  - community.dns._infomaniak.record_type_choices_record_sets_module
  - community.dns._infomaniak.record_type_seealso
  - community.dns._infomaniak.zone_id_type
  - community.dns._module_record_sets
  - community.dns._options.record_transformation
  - community.dns._attributes
  - community.dns._attributes.actiongroup_infomaniak
  - community.dns._zone_name_id.combined_modify

author:
  - Felix Fontein (@felixfontein)
"""

EXAMPLES = r"""
- name: Make sure some records exist and have the expected values
  community.dns.infomaniak_dns_record_sets:
    zone: foo.com
    records:
      - prefix: new
        type: A
        ttl: 7200
        value:
          - 1.1.1.1
          - 2.2.2.2
      - prefix: new
        type: AAAA
        ttl: 7200
        value:
          - "::1"
      - record: foo.com
        type: TXT
        value:
          - test
    infomaniak_token: access_token

- name: Synchronize DNS zone with a fixed set of records
  # If a record exists that is not mentioned here, it will be deleted
  community.dns.infomaniak_dns_record_sets:
    zone: foo.com
    purge: true
    records:
      - prefix: ''
        type: A
        value: 127.0.0.1
      - prefix: ''
        type: AAAA
        value: "::1"
      - prefix: ''
        type: NS
        value:
          - ns-1.infomaniak.com
          - ns-2.infomaniak.com
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
from ansible_collections.community.dns.plugins.module_utils._module.record_sets import (
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
