# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    zone_name:
        description:
          - The DNS zone to query.
          - Exactly one of I(zone_name) and I(zone_id) must be specified.
        type: str
        aliases:
          - zone
    zone_id:
        description:
          - The ID of the DNS zone to query.
          - Exactly one of I(zone_name) and I(zone_id) must be specified.
        version_added: 0.2.0

notes:
    - "Supports C(check_mode)."
'''
