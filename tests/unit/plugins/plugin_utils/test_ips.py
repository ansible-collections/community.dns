# -*- coding: utf-8 -*-
# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest
from ansible.errors import AnsibleError
from ansible_collections.community.dns.plugins.plugin_utils import ips
from ansible_collections.community.dns.plugins.plugin_utils.ips import (
    assert_requirements_present,
)


# We need ipaddress
ipaddress = pytest.importorskip("ipaddress")


def test_assert_requirements_present() -> None:
    orig_importerror = ips.IPADDRESS_IMPORT_EXC
    try:
        ips.IPADDRESS_IMPORT_EXC = None
        assert_requirements_present("community.dns.foo", "lookup")

        ips.IPADDRESS_IMPORT_EXC = ImportError("ipaddress")
        with pytest.raises(AnsibleError) as exc:
            assert_requirements_present("community.dns.foo", "lookup")

        assert "ipaddress" in exc.value.args[0]

    finally:
        ips.IPADDRESS_IMPORT_EXC = orig_importerror
