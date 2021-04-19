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

from ansible_collections.community.dns.plugins.module_utils.module._utils import (
    normalize_dns_name,
    get_prefix,
)


def test_normalize_dns_name():
    assert normalize_dns_name('ExAMPLE.CoM.') == 'example.com'
    assert normalize_dns_name('EXAMpLE.CoM') == 'example.com'
    assert normalize_dns_name('Example.com') == 'example.com'
    assert normalize_dns_name('.') == ''


def test_get_prefix():
    assert get_prefix('example.com', 'example.com') is None
    assert get_prefix('www.example.com', 'example.com') == 'www'
    with pytest.raises(DNSAPIError):
        get_prefix('example.org', 'example.com')
    with pytest.raises(DNSAPIError):
        get_prefix('wwwexample.com', 'example.com')
