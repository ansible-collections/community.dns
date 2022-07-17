# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
name: hetzner_dns_records

short_description: Create inventory from Hetzner DNS records

version_added: 2.0.0

extends_documentation_fragment:
    - community.dns.hetzner
    - community.dns.hetzner.plugin
    - community.dns.hetzner.record_type_choices_records_inventory
    - community.dns.hetzner.zone_id_type
    - community.dns.inventory_records
    - community.dns.options.record_transformation

notes:
    - The provider-specific I(hetzner_token) option can be templated.

author:
    - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
    - Felix Fontein (@felixfontein)
'''

from ansible_collections.community.dns.plugins.module_utils.http import (
    OpenURLHelper,
)

from ansible_collections.community.dns.plugins.module_utils.hetzner.api import (
    create_hetzner_api,
    create_hetzner_provider_information,
)

from ansible_collections.community.dns.plugins.plugin_utils.templated_options import (
    TemplatedOptionProvider,
)

from ansible_collections.community.dns.plugins.plugin_utils.inventory.records import (
    RecordsInventoryModule,
)


class InventoryModule(RecordsInventoryModule):
    NAME = 'community.dns.hetzner_dns_records'
    VALID_ENDINGS = ('hetzner_dns.yaml', 'hetzner_dns.yml')

    def setup_api(self):
        self.provider_information = create_hetzner_provider_information()
        self.api = create_hetzner_api(TemplatedOptionProvider(self, self.templar), OpenURLHelper())
