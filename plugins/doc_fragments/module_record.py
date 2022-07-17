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
description:
    - Records are matched by prefix / record name and value.

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
    ttl:
        description:
          - The TTL to give the new record, in seconds.
          - This is not used for record deletion.
        type: int
    type:
        description:
          - The type of DNS record to create or delete.
        required: true
        type: str
    value:
        description:
          - The new value when creating a DNS record.
          - When deleting a record all values for the record must be specified or it will
            not be deleted.
        required: true
        type: str

notes:
    - "Supports C(check_mode) and C(--diff)."
'''
