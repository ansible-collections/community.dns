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
    what:
        description:
        - Describes whether to fetch a single record and type combination, all types for a
          record, or all records. By default, a single record and type combination is fetched.
        - Note that the return value structure depends on this option.
        choices: ['single_record', 'all_types_for_record', 'all_records']
        default: single_record
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
    record:
        description:
        - The full DNS record to retrieve.
        - Required if I(what) is C(single_record) or C(all_types_for_record).
        type: str
    type:
        description:
        - The type of DNS record to retrieve.
        - Required if I(what) is C(single_record).
        choices: ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
        type: str

notes:
    - "Supports C(check_mode)."
'''
