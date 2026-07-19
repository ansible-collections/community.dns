# Copyright (c) 2026 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
name: infomaniak_dns_records

short_description: Create inventory from Infomaniak DNS records

version_added: 4.1.0

description:
  - This plugin allows to create an inventory from Infomaniak DNS records.
  - 'For Ansible to be able to identify a YAML file as an inventory for this plugin, the inventory file must contain C(plugin:
    community.dns.infomaniak_dns_records) and its filename must end with C(infomaniak_dns.yaml) or C(infomaniak_dns.yml).'
options:
  plugin:
    description: The name of this plugin. Should always be set to V(community.dns.infomaniak_dns_records) for this plugin to
      recognize it as its own.
    required: true
    choices:
      - community.dns.infomaniak_dns_records
    type: str

extends_documentation_fragment:
  - community.dns._infomaniak
  - community.dns._infomaniak.plugin
  - community.dns._infomaniak.record_type_choices_records_inventory
  - community.dns._infomaniak.record_type_seealso
  - community.dns._infomaniak.zone_id_type
  - community.dns._inventory_records
  - community.dns._options.record_transformation
  - community.library_inventory_filtering_v1.inventory_filter

notes:
  - The provider-specific O(infomaniak_token) option can be templated.
author:
  - Felix Fontein (@felixfontein)

seealso:
  - module: community.dns.infomaniak_dns_record_set_info
  - module: community.dns.infomaniak_dns_record_info
"""

EXAMPLES = r"""
# filename must end with infomaniak_dns.yaml or infomaniak_dns.yml

plugin: community.dns.infomaniak_dns_records
zone_name: domain.ch
simple_filters:
  type:
    - TXT
filters:
  - include: >-
      not ansible_host.startswith('v=')
  - exclude: true
txt_transformation: unquoted

# You can also configure the token by putting secret value into this file,
# but this is discouraged. Use a lookup like below, or leave it away and
# set it with the INFOMANIAK_DNS_TOKEN environment variable.
infomaniak_token: >-
  {{ (lookup('community.sops.sops', 'keys/infomaniak.sops.yml') | from_yaml).infomaniak_dns_token }}
"""

import typing as t

from ansible_collections.community.dns.plugins.module_utils._http import OpenURLHelper
from ansible_collections.community.dns.plugins.module_utils._infomaniak.api import (
    create_infomaniak_api,
    create_infomaniak_provider_information,
)
from ansible_collections.community.dns.plugins.plugin_utils._inventory.records import (
    RecordsInventoryModule,
)
from ansible_collections.community.dns.plugins.plugin_utils._templated_options import (
    TemplatedOptionProvider,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from ..module_utils._provider import ProviderInformation
    from ..module_utils._zone_record_api import ZoneRecordAPI
    from ..module_utils._zone_record_set_api import ZoneRecordSetAPI


class InventoryModule(RecordsInventoryModule):
    NAME = "community.dns.infomaniak_dns_records"
    VALID_ENDINGS = ("infomaniak_dns.yaml", "infomaniak_dns.yml")

    def setup_api(self) -> tuple[ProviderInformation, ZoneRecordAPI | ZoneRecordSetAPI]:
        option_provider = TemplatedOptionProvider(self, self.templar)
        provider_information = create_infomaniak_provider_information(
            option_provider=option_provider
        )
        return provider_information, create_infomaniak_api(
            option_provider, OpenURLHelper()
        )
