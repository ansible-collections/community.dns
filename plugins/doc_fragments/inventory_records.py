# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
description:
    - Records are matched by prefix / record name and value.

notes:
    - The I(zone_name) and I(zone_id) options can be templated.

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
    filters:
        description:
          - A dictionary of filter value pairs.
        type: dict
        default: {}
        suboptions:
            # (The following must be kept in sync with the equivalent lines in <provider_name>.py!)
            type:
                description:
                  - Record types whose values to use.
                type: list
                elements: string
                default: [A, AAAA, CNAME]
'''
