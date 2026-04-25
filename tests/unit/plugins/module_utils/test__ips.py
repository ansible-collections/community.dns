# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.community.dns.plugins.module_utils._ips import (
    is_ip_address,
)

IS_IP_ADDRESS_DATA = [
    ("foo.bar", False),
    ("foo", False),
    ("123", False),
    ("1.2.3.4", True),
    ("::", True),
]


@pytest.mark.parametrize("input_string, output", IS_IP_ADDRESS_DATA)
def test_is_ip_address(input_string, output):
    assert is_ip_address(input_string) == output
