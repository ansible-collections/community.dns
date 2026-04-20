# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this doc fragment is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r"""
attributes:
  idempotent:
    support: full
options:
  zone_name:
    description:
      - The DNS zone to query.
      - Exactly one of O(zone_name) and O(zone_id) must be specified.
    type: str
    aliases:
      - zone
  zone_id:
    description:
      - The ID of the DNS zone to query.
      - Exactly one of O(zone_name) and O(zone_id) must be specified.
    version_added: 0.2.0
"""
