# Copyright (c) 2026 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this doc fragment is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations


class ModuleDocFragment:
    COMBINED_MODIFY = r"""
options:
  zone_name:
    description:
      - The DNS zone to modify.
      - Exactly one of O(zone_name) and O(zone_id) must be specified.
    type: str
    aliases:
      - zone
  zone_id:
    description:
      - The ID of the DNS zone to modify.
      - Exactly one of O(zone_name) and O(zone_id) must be specified.
"""

    COMBINED_QUERY = r"""
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
"""

    NAME_ONLY_MODIFY = r"""
options:
  zone_name:
    description:
      - The DNS zone to modify.
      - Note that the API does not allow to query by zone ID.
        Therefore, O(zone_id) is an alias of O(zone_name) for compatibility with modules and plugins for other providers.
    type: str
    aliases:
      - zone
      - zone_id
    required: true
"""

    NAME_ONLY_QUERY = r"""
options:
  zone_name:
    description:
      - The DNS zone to query.
      - Note that the API does not allow to query by zone ID.
        Therefore, O(zone_id) is an alias of O(zone_name) for compatibility with modules and plugins for other providers.
    type: str
    aliases:
      - zone
      - zone_id
    required: true
"""
