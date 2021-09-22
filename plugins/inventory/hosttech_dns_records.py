# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
name: hosttech_dns_records

short_description: Create inventory from Hosttech DNS records

version_added: 2.0.0

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.hosttech.plugin
    - community.dns.hosttech.record_type_choices_records_inventory
    - community.dns.hosttech.zone_id_type
    - community.dns.inventory_records
    - community.dns.options.record_transformation

author:
    - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
    - Felix Fontein (@felixfontein)
'''

from ansible_collections.community.dns.plugins.module_utils.http import (
    OpenURLHelper,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    create_hosttech_api,
    create_hosttech_provider_information,
)

from ansible_collections.community.dns.plugins.plugin_utils.inventory.records import (
    RecordsInventoryModule,
)


class InventoryModule(RecordsInventoryModule):
    NAME = 'community.dns.hosttech_dns_records'
    VALID_ENDINGS = ('hosttech_dns.yaml', 'hosttech_dns.yml')

    def setup_api(self):
        self.provider_information = create_hosttech_provider_information()
        self.api = create_hosttech_api(self, OpenURLHelper())
