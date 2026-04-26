# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import ipaddress

from ansible.module_utils.common.text.converters import to_text


def is_ip_address(server: str | bytes) -> bool:
    try:
        ipaddress.ip_address(to_text(server))
        return True
    except ValueError:
        return False
