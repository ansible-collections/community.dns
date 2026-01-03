# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)

from ansible_collections.community.dns.plugins.module_utils.http import OpenURLHelper
from ansible_collections.community.dns.plugins.module_utils.json_api_helper import (
    JSONAPIHelper,
    _get_header_value,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)


def test_get_header_value():
    assert _get_header_value({'Return-Type': 1}, 'return-type') == 1
    assert _get_header_value({'Return-Type': 1}, 'Return-Type') == 1
    assert _get_header_value({'return-Type': 1}, 'Return-type') == 1
    assert _get_header_value({'return_type': 1}, 'Return-type') is None


def test_extract_error_message():
    api = JSONAPIHelper(MagicMock(), '123', 'https://example.com')
    assert api._extract_error_message(None) == ''
    assert api._extract_error_message('foo') == " with data: 'foo'"
    assert api._extract_error_message({}) == ' with data: {}'
    assert api._extract_error_message({'message': ''}) == " with data: {'message': ''}"
    assert api._extract_error_message({'message': 'foo'}) == " with data: {'message': 'foo'}"


def test_validate():
    module = MagicMock()
    api = JSONAPIHelper(module, '123', 'https://example.com')
    with pytest.raises(DNSAPIError) as exc:
        api._validate()
    assert exc.value.args[0] == 'Internal error: info needs to be provided'


def test_process_json_result():
    http_helper = MagicMock()
    api = JSONAPIHelper(http_helper, '123', 'https://example.com')
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content=None, info={'status': 401, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Unauthorized: the authentication parameters are incorrect (HTTP status 401)'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{"message": ""}'.encode('utf-8'), info={'status': 401, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Unauthorized: the authentication parameters are incorrect (HTTP status 401)'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{"message": "foo"}'.encode('utf-8'), info={'status': 401, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Unauthorized: the authentication parameters are incorrect (HTTP status 401): foo'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content=None, info={'status': 403, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Forbidden: you do not have access to this resource (HTTP status 403)'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{"message": ""}'.encode('utf-8'), info={'status': 403, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Forbidden: you do not have access to this resource (HTTP status 403)'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{"message": "foo"}'.encode('utf-8'), info={'status': 403, 'url': 'https://example.com'})
    assert exc.value.args[0] == 'Forbidden: you do not have access to this resource (HTTP status 403): foo'

    info = {'status': 200, 'url': 'https://example.com'}
    info['content-TYPE'] = 'application/json'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='not JSON'.encode('utf-8'), info=info)
    assert exc.value.args[0] == 'GET https://example.com did not yield JSON data, but HTTP status code 200 with data: not JSON'

    info = {'status': 200, 'url': 'https://example.com'}
    info['Content-type'] = 'application/json'
    r, i = api._process_json_result(content='not JSON'.encode('utf-8'), info=info, must_have_content=False)
    assert r is None
    info = {'status': 200, 'url': 'https://example.com'}
    info['Content-type'] = 'application/json'
    assert i == info

    info = {'status': 404, 'url': 'https://example.com'}
    info['content-type'] = 'application/json'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{}'.encode('utf-8'), info=info)
    assert exc.value.args[0] == 'Expected successful HTTP status for GET https://example.com, but got HTTP status 404 (Not found) with data: {}'

    info = {'status': 404, 'url': 'https://example.com'}
    info['content-type'] = 'application/json'
    with pytest.raises(DNSAPIError) as exc:
        api._process_json_result(content='{}'.encode('utf-8'), info=info, expected=[200, 201])
    assert exc.value.args[0] == 'Expected HTTP status 200, 201 for GET https://example.com, but got HTTP status 404 (Not found) with data: {}'


def test__request(mocker):
    def is_rate_limiting_result(content, info):
        return info['status'] == 429

    mock_sleep = MagicMock(return_value=None)
    mocker.patch("time.sleep", mock_sleep)
    open_url = OpenUrlProxy(
        [
            OpenUrlCall("GET", 429)
            .expect_url("https://example.com/foo")
            .result_str("first"),
            OpenUrlCall("GET", 200)
            .expect_url("https://example.com/foo")
            .result_str("second"),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    api_helper = JSONAPIHelper(OpenURLHelper(), "foo", "https://example.com")
    api_helper._is_rate_limiting_result = is_rate_limiting_result
    result, _info = api_helper._request("https://example.com/foo")
    open_url.assert_is_done()
    assert result == b'second'
    mock_sleep.assert_called_once_with(10)


def test__post__put_no_data(mocker):
    def no_content(content):
        return content is None

    open_url = OpenUrlProxy(
        [
            OpenUrlCall("POST", 200)
            .expect_header('accept', 'application/json')
            .expect_url("https://example.com/foo")
            .expect_content_predicate(no_content)
            .return_header('Content-Type', 'application/json')
            .result_json({}),
            OpenUrlCall("PUT", 200)
            .expect_header('accept', 'application/json')
            .expect_url("https://example.com/bar")
            .expect_content_predicate(no_content)
            .return_header('Content-Type', 'application/json')
            .result_json({}),
        ]
    )
    mocker.patch(
        "ansible_collections.community.dns.plugins.module_utils.http.open_url", open_url
    )
    api_helper = JSONAPIHelper(OpenURLHelper(), "foo", "https://example.com")
    api_helper._post("/foo")
    api_helper._put("/bar")
    open_url.assert_is_done()
