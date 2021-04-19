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
    module = MagicMock()
    module.params = {'hosttech_username': None, 'hosttech_token': None}
    with pytest.raises(DNSAPIError) as exc:
        api.create_hosttech_api(module)
    assert exc.value.args[0] == 'Internal error!'


class FailJsonException(Exception):
    def __init__(self, data):
        self.data = data


def fake_fail(**kwargs):
    raise FailJsonException(kwargs)


def test_wsdl_missing():
    old_value = api.HAS_LXML_ETREE
    try:
        api.HAS_LXML_ETREE = False
        module = MagicMock()
        module.params = {'hosttech_username': '', 'hosttech_password': '', 'hosttech_token': None}
        module.fail_json = MagicMock(side_effect=fake_fail)
        with pytest.raises(FailJsonException) as exc:
            api.create_hosttech_api(module)
        assert exc.value.args[0]['msg'] == 'Needs lxml Python module (pip install lxml)'
    finally:
        api.HAS_LXML_ETREE = old_value
