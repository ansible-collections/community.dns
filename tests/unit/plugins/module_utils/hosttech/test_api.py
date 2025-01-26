# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils.hosttech import api
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
)

from ..helper import CustomProvideOptions


def test_internal_error():
    option_provider = CustomProvideOptions({})
    with pytest.raises(DNSAPIError) as exc:
        api.create_hosttech_api(option_provider, MagicMock())
    assert exc.value.args[0] == 'One of hosttech_token or both hosttech_username and hosttech_password must be provided!'


def test_wsdl_missing():
    option_provider = CustomProvideOptions({
        'hosttech_username': 'foo',
        'hosttech_password': 'foo',
    })
    old_value = api.HAS_LXML_ETREE
    try:
        api.HAS_LXML_ETREE = False
        with pytest.raises(DNSAPIError) as exc:
            api.create_hosttech_api(option_provider, MagicMock())
        assert exc.value.args[0] == 'Needs lxml Python module (pip install lxml)'
    finally:
        api.HAS_LXML_ETREE = old_value
