# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
name: hosttech_dns_records

short_description: Create inventory from Hosttech DNS records

version_added: 2.0.0

options:
    # We need to overwrite zone_id to be of type string, otherwise templating cannot be passed in
    zone_id:
        type: raw
        # If there wouldn't be ansible-base 2.10, this should be string instead. ansible-base will
        # not accept an integer for type=string options, whence type=string breaks backwards
        # compatibility with previous type=int...
        #   type: string

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.hosttech.plugin
    - community.dns.hosttech.record_type_choices_records_inventory
    - community.dns.hosttech.zone_id_type
    - community.dns.inventory_records
    - community.dns.options.record_transformation

notes:
    - The provider-specific I(hosttech_username), I(hosttech_password), and I(hosttech_token) options can be templated.

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

from ansible_collections.community.dns.plugins.plugin_utils.templated_options import (
    TemplatedOptionProvider,
)

from ansible_collections.community.dns.plugins.plugin_utils.inventory.records import (
    RecordsInventoryModule,
)


class InventoryModule(RecordsInventoryModule):
    NAME = 'community.dns.hosttech_dns_records'
    VALID_ENDINGS = ('hosttech_dns.yaml', 'hosttech_dns.yml')

    def setup_api(self):
        self.provider_information = create_hosttech_provider_information()
        self.api = create_hosttech_api(TemplatedOptionProvider(self, self.templar), OpenURLHelper())
