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
          - Exactly one of I(zone) and I(zone_id) must be specified.
        type: str
    zone_id:
        description:
          - The ID of the DNS zone to modify.
          - Exactly one of I(zone) and I(zone_id) must be specified.
        version_added: 0.2.0
    record:
        description:
          - The full DNS record to create or delete.
          - Exactly one of I(record) and I(prefix) must be specified.
        type: str
    prefix:
        description:
          - The prefix of the DNS record.
          - This is the part of I(record) before I(zone). For example, if the record to be modified is C(www.example.com)
            for the zone C(example.com), the prefix is C(www). If the record in this example would be C(example.com), the
            prefix would be C('') (empty string).
          - Exactly one of I(record) and I(prefix) must be specified.
        type: str
        version_added: 0.2.0
    ttl:
        description:
          - The TTL to give the new record, in seconds.
        default: 3600
        type: int
    type:
        description:
          - The type of DNS record to create or delete.
        required: true
        type: str
    value:
        description:
          - The new value when creating a DNS record.
          - YAML lists or multiple comma-spaced values are allowed.
          - When deleting a record all values for the record must be specified or it will
            not be deleted.
          - Must be specified if I(state=present) or I(overwrite=false).
        type: list
        elements: str
    overwrite:
        description:
          - If I(state=present), whether an existing record should be overwritten on create if values do not
            match.
          - If I(state=absent), whether existing records should be deleted if values do not match.
        default: false
        type: bool

notes:
    - "Supports C(check_mode) and C(--diff)."
'''
