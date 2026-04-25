# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import traceback
import typing as t

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_text

IPADDRESS_IMPORT_EXC: str | None
try:
    import ipaddress
except ImportError:
    IPADDRESS_IMPORT_EXC = traceback.format_exc()
else:
    IPADDRESS_IMPORT_EXC = None

if t.TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule  # pragma: no cover


def is_ip_address(server: str | bytes) -> bool:
    try:
        ipaddress.ip_address(to_text(server))
        return True
    except ValueError:
        return False


def assert_requirements_present(module: AnsibleModule) -> None:
    if IPADDRESS_IMPORT_EXC is not None:
        module.fail_json(
            msg=missing_required_lib("ipaddress"),
            exception=IPADDRESS_IMPORT_EXC,
        )
