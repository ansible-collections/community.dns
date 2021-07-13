# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import MagicMock, patch

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech import api


def test_internal_error():
    def get_option(option_name):
        return None

    option_provider = MagicMock()
    option_provider.get_option = get_option
    with pytest.raises(DNSAPIError) as exc:
        api.create_hosttech_api(option_provider, MagicMock())
    assert exc.value.args[0] == 'One of hosttech_token or both hosttech_username and hosttech_password must be provided!'


def test_wsdl_missing():
    def get_option(option_name):
        if option_name in ('hosttech_username', 'hosttech_password'):
            return 'foo'
        return None

    option_provider = MagicMock()
    option_provider.get_option = get_option
    old_value = api.HAS_LXML_ETREE
    try:
        api.HAS_LXML_ETREE = False
        with pytest.raises(DNSAPIError) as exc:
            api.create_hosttech_api(option_provider, MagicMock())
        assert exc.value.args[0] == 'Needs lxml Python module (pip install lxml)'
    finally:
        api.HAS_LXML_ETREE = old_value
