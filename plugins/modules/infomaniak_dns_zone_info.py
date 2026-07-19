#!/usr/bin/python
# Copyright (c) 2026 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: infomaniak_dns_zone_info

short_description: Retrieve zone information in Infomaniak DNS service

version_added: 4.1.0

description:
  - Retrieves zone information in Infomaniak DNS service.
extends_documentation_fragment:
  - community.dns._infomaniak
  - community.dns._module_zone_info
  - community.dns._attributes
  - community.dns._attributes.actiongroup_infomaniak
  - community.dns._attributes.info_module
  - community.dns._attributes.idempotent_not_modify_state
  - community.dns._zone_name_id.name_only_query

author:
  - Felix Fontein (@felixfontein)
"""

EXAMPLES = r"""
- name: Retrieve details for foo.com zone
  community.dns.infomaniak_dns_zone_info:
    zone: foo.com
    infomaniak_token: access_token
  register: rec
"""

RETURN = r"""
zone_name:
  description: The name of the zone.
  type: int
  returned: success
  sample: example.com

zone_id:
  description:
    - The ID of the zone.
    - Note that Infomaniak's API does not support accessing by zone ID,
      whence we use the zone's name as the "ID" for purposes of the collection's interface.
      The actual zone ID can be taken from RV(zone_info.id).
  type: str
  returned: success
  sample: foo.com

zone_info:
  description:
    - Extra information returned by the API.
  type: dict
  returned: success
  contains:
    dnssec:
      description:
        - Information on DNSSEC.
      type: dict
      contains:
        is_enabled:
          description:
            - Whether DNSSEC is enabled for the domain.
          type: bool
          sample: true
      sample:
        is_enabled: true
    id:
      description:
        - The actual zone ID. See RV(zone_id) for more information.
      type: int
      sample: 1234
    nameservers:
      description:
        - List of nameservers the zone should have for using Infomaniak's DNS.
      type: list
      elements: str
      sample:
        - ns1.infomaniak.com
        - ns2.infomaniak.com
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
from ansible_collections.community.dns.plugins.module_utils._module.zone_info import (
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
