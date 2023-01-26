# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
requirements:
    - lxml

options:
    hosttech_username:
        description:
          - The username for the Hosttech API user.
          - If provided, I(hosttech_password) must also be provided.
          - Mutually exclusive with I(hosttech_token).
        type: str
    hosttech_password:
        description:
          - The password for the Hosttech API user.
          - If provided, I(hosttech_username) must also be provided.
          - Mutually exclusive with I(hosttech_token).
        type: str
    hosttech_token:
        description:
          - The password for the Hosttech API user.
          - Mutually exclusive with I(hosttech_username) and I(hosttech_password).
          - Since community.dns 1.2.0, the alias I(api_token) can be used.
        aliases:
          - api_token
        type: str
        version_added: 0.2.0
'''

    # NOTE: This document fragment augments the above standard DOCUMENTATION document fragment
    #       by providing alternative ways to provide configuration for plugins. (The above
    #       documentation fragment is tailored for modules.)
    PLUGIN = r'''
options:
    hosttech_username:
        env:
          - name: ANSIBLE_HOSTTECH_API_USERNAME
            version_added: 2.5.0
    hosttech_password:
        env:
          - name: ANSIBLE_HOSTTECH_API_PASSWORD
            version_added: 2.5.0
    hosttech_token:
        env:
          - name: ANSIBLE_HOSTTECH_DNS_TOKEN
            version_added: 2.5.0
'''

    # WARNING: This section is automatically generated by update-docs-fragments.py.
    #          It is used to augment the docs fragments module_record, module_record_set.
    #          DO NOT EDIT MANUALLY!
    RECORD_DEFAULT_TTL = r'''
options:
    ttl:
        default: 3600
'''

    # WARNING: This section is automatically generated by update-docs-fragments.py.
    #          It is used to augment the docs fragments module_record, module_record_info,
    #          module_record_set, module_record_set_info.
    #          DO NOT EDIT MANUALLY!
    RECORD_TYPE_CHOICES = r'''
options:
    type:
        choices:
          - A
          - AAAA
          - CAA
          - CNAME
          - MX
          - NS
          - PTR
          - SPF
          - SRV
          - TXT
'''

    # WARNING: This section is automatically generated by update-docs-fragments.py.
    #          It is used to augment the docs fragment module_record_sets.
    #          DO NOT EDIT MANUALLY!
    RECORD_TYPE_CHOICES_RECORD_SETS_MODULE = r'''
options:
    record_sets:
        suboptions:
            record:
                description:
                  - The full DNS record to create or delete.
                  - Exactly one of I(record) and I(prefix) must be specified.
                type: str
            prefix:
                description:
                  - The prefix of the DNS record.
                  - This is the part of I(record) before I(zone_name). For example,
                      if the record to be modified is C(www.example.com) for the zone
                      C(example.com), the prefix is C(www). If the record in this
                      example would be C(example.com), the prefix would be C('') (empty
                      string).
                  - Exactly one of I(record) and I(prefix) must be specified.
                type: str
            ttl:
                description:
                  - The TTL to give the new record, in seconds.
                type: int
                default: 3600
            type:
                description:
                  - The type of DNS record to create or delete.
                required: true
                type: str
                choices:
                  - A
                  - AAAA
                  - CAA
                  - CNAME
                  - MX
                  - NS
                  - PTR
                  - SPF
                  - SRV
                  - TXT
            value:
                description:
                  - The new value when creating a DNS record.
                  - YAML lists or multiple comma-spaced values are allowed.
                  - When deleting a record all values for the record must be specified
                      or it will not be deleted.
                  - Must be specified if I(ignore=false).
                type: list
                elements: str
            ignore:
                description:
                  - If set to C(true), I(value) will be ignored.
                  - This is useful when I(prune=true), but you do not want certain
                      entries to be removed without having to know their current value.
                type: bool
                default: false
'''

    # WARNING: This section is automatically generated by update-docs-fragments.py.
    #          It is used to augment the docs fragment inventory_records.
    #          DO NOT EDIT MANUALLY!
    RECORD_TYPE_CHOICES_RECORDS_INVENTORY = r'''
options:
    filters:
        suboptions:
            type:
                description:
                  - Record types whose values to use.
                type: list
                elements: string
                default:
                  - A
                  - AAAA
                  - CNAME
                choices:
                  - A
                  - AAAA
                  - CAA
                  - CNAME
                  - MX
                  - NS
                  - PTR
                  - SPF
                  - SRV
                  - TXT
'''

    # WARNING: This section is automatically generated by update-docs-fragments.py.
    #          It is used to augment the docs fragments inventory_records, module_record,
    #          module_record_info, module_record_set, module_record_set_info,
    #          module_record_sets, module_zone_info.
    #          DO NOT EDIT MANUALLY!
    ZONE_ID_TYPE = r'''
options:
    zone_id:
        type: int
'''
