# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
description:
    - The module allows to set, modify and delete multiple DNS record sets at once.
    - With the I(purge) option, it is also possible to delete existing record sets
      that are not mentioned in the module parameters. With this, it is possible
      to synchronize the expected state of a DNS zone with the expected state.
    - "It is possible to ignore certain record sets by specifying I(ignore: true) for
       that record set."

options:
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
    prune:
        description:
          - If set to C(true), will remove all existing records in the zone that are not listed in I(records).
        type: bool
        default: false
    record_sets:
        description:
          - The records that should be present in the zone.
        required: true
        type: list
        elements: dict
        aliases:
          - records
        suboptions:
            # (The following must be kept in sync with the equivalent lines in <provider_name>.py!)
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
                  - Must be specified if I(ignore=false).
                type: list
                elements: str
            ignore:
                description:
                  - If set to C(true), I(value) will be ignored.
                  - This is useful when I(prune=true), but you do not want certain entries to be removed
                    without having to know their current value.
                type: bool
                default: false

notes:
    - "Supports C(check_mode) and C(--diff)."
'''
