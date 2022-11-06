# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment

    # NOTE: This document fragment needs to be augmented by ZONE_ID_TYPE in a provider document fragment.
    #       The ZONE_ID_TYPE fragment will provide `choices` for the options.type entry.
    DOCUMENTATION = r'''
options:
    state:
        description:
          - Specifies the state of the resource record.
        required: true
        choices: ['present', 'absent']
        type: str
    zone_name:
        description:
          - The DNS zone to modify.
          - Exactly one of I(zone_name) and I(zone_id) must be specified.
        type: str
        aliases:
          - zone
    zone_id:
        description:
          - The ID of the DNS zone to modify.
          - Exactly one of I(zone_name) and I(zone_id) must be specified.
        version_added: 0.2.0
    record:
        description:
          - The full DNS record to create or delete.
          - Exactly one of I(record) and I(prefix) must be specified.
        type: str
    prefix:
        description:
          - The prefix of the DNS record.
          - This is the part of I(record) before I(zone_name). For example, if the record to be modified is C(www.example.com)
            for the zone C(example.com), the prefix is C(www). If the record in this example would be C(example.com), the
            prefix would be C('') (empty string).
          - Exactly one of I(record) and I(prefix) must be specified.
        type: str
        version_added: 0.2.0
    ttl:
        description:
          - The TTL to give the new record, in seconds.
          - Will be ignored if I(state=absent) and I(on_existing=replace).
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
          - Must be specified if I(state=present) or when I(on_existing) is not C(replace).
          - Will be ignored if I(state=absent) and I(on_existing=replace).
        type: list
        elements: str
    on_existing:
        description:
          - This option defines the behavior if the record set already exists, but differs from the specified record set.
            For this comparison, I(value) and I(ttl) are used for all records of type I(type) matching the I(prefix) resp. I(record).
          - If set to C(replace), the record will be updated (I(state=present)) or removed (I(state=absent)).
            This is the old I(overwrite=true) behavior.
          - If set to C(keep_and_fail), the module will fail and not modify the records.
            This is the old I(overwrite=false) behavior if I(state=present).
          - If set to C(keep_and_warn), the module will warn and not modify the records.
          - If set to C(keep), the module will not modify the records.
            This is the old I(overwrite=false) behavior if I(state=absent).
          - If I(state=absent) and the value is not C(replace), I(value) must be specified.
        default: replace
        type: str
        choices:
          - replace
          - keep_and_fail
          - keep_and_warn
          - keep
'''
