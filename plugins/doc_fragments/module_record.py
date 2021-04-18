# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    state:
        description:
        - Specifies the state of the resource record.
        required: true
        choices: ['present', 'absent']
        type: str
    zone:
        description:
        - The DNS zone to modify.
        required: true
        type: str
    record:
        description:
        - The full DNS record to create or delete.
        required: true
        type: str
    ttl:
        description:
        - The TTL to give the new record, in seconds.
        default: 3600
        type: int
    type:
        description:
        - The type of DNS record to create or delete.
        required: true
        choices: ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
        type: str
    value:
        description:
        - The new value when creating a DNS record.
        - YAML lists or multiple comma-spaced values are allowed.
        - When deleting a record all values for the record must be specified or it will
          not be deleted.
        required: true
        type: list
        elements: str
    overwrite:
        description:
        - Whether an existing record should be overwritten on create if values do not
          match.
        default: false
        type: bool

notes:
    - "Supports C(check_mode) and C(--diff)."
'''
