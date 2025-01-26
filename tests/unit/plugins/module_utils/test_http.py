# -*- coding: utf-8 -*-
# Copyright (c) 2025, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible.module_utils.urls import ConnectionError, NoSSLError
from ansible_collections.community.dns.plugins.module_utils.http import (
    NetworkError,
    OpenURLHelper,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)


def test_open_url_helper_1(mocker):
    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 400)
        .expect_url('https://dns.hetzner.com/api/v1/zones')
        .result_error(body='foo'),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    helper = OpenURLHelper()
    content, info = helper.fetch_url('https://dns.hetzner.com/api/v1/zones')
    open_url.assert_is_done()
    assert content == 'foo'
    assert info == {
        'status': 400,
    }


def test_open_url_helper_2(mocker):
    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 400)
        .expect_url('https://dns.hetzner.com/api/v1/zones')
        .result_error(),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    helper = OpenURLHelper()
    content, info = helper.fetch_url('https://dns.hetzner.com/api/v1/zones')
    open_url.assert_is_done()
    assert content == ''
    assert info == {
        'status': 400,
    }


def test_open_url_helper_3(mocker):
    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 400)
        .expect_url('https://dns.hetzner.com/api/v1/zones')
        .exception(lambda: NoSSLError('foo')),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    helper = OpenURLHelper()
    with pytest.raises(NetworkError) as exc:
        helper.fetch_url('https://dns.hetzner.com/api/v1/zones')
    open_url.assert_is_done()
    print(exc.value.args[0])
    assert exc.value.args[0] == 'Cannot connect via SSL: foo'


def test_open_url_helper_4(mocker):
    open_url = OpenUrlProxy([
        OpenUrlCall('GET', 400)
        .expect_url('https://dns.hetzner.com/api/v1/zones')
        .exception(lambda: ConnectionError('foo')),
    ])
    mocker.patch('ansible_collections.community.dns.plugins.module_utils.http.open_url', open_url)
    helper = OpenURLHelper()
    with pytest.raises(NetworkError) as exc:
        helper.fetch_url('https://dns.hetzner.com/api/v1/zones')
    open_url.assert_is_done()
    print(exc.value.args[0])
    assert exc.value.args[0] == 'Connection error: foo'
