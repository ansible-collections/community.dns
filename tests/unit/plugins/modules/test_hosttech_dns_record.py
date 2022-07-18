# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from ansible_collections.community.dns.plugins.modules import hosttech_dns_record

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa

from .hosttech import (
    expect_wsdl_authentication,
    expect_wsdl_value,
    validate_wsdl_call,
    validate_wsdl_add_request,
    validate_wsdl_del_request,
    create_wsdl_add_result,
    create_wsdl_del_result,
    HOSTTECH_WSDL_DEFAULT_ENTRIES,
    HOSTTECH_WSDL_DEFAULT_ZONE_RESULT,
    HOSTTECH_WSDL_ZONE_NOT_FOUND,
    HOSTTECH_JSON_DEFAULT_ENTRIES,
    HOSTTECH_JSON_ZONE_GET_RESULT,
    HOSTTECH_JSON_ZONE_LIST_RESULT,
    HOSTTECH_JSON_ZONE_RECORDS_GET_RESULT,
)

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False


@pytest.mark.skipif(not HAS_LXML_ETREE, reason="Need lxml.etree for WSDL tests")
class TestHosttechDNSRecordWSDL(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.org',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_ZONE_NOT_FOUND),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    '23',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_ZONE_NOT_FOUND),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id_prefix(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_id': 23,
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    '23',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_ZONE_NOT_FOUND),
        ])

        assert result['msg'] == 'Zone not found'

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 3600,
            'value': '1.2.3.6',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_absent_type(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_id': 42,
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    '42',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_absent_record(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': '1.2.3.6',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_absent(self, mocker):
        record = HOSTTECH_WSDL_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record[3] + 'example.com',
            'type': record[2],
            'value': record[4],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_del_request(record),
            ]))
            .result_str(create_wsdl_del_result(True)),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one(self, mocker):
        new_entry = (131, 42, 'CAA', 'foo', '0 issue "letsencrypt.org"', 3600, None, None)
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'foo.example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(HOSTTECH_WSDL_DEFAULT_ZONE_RESULT),
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_add_request('42', new_entry),
            ]))
            .result_str(create_wsdl_add_result(new_entry)),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42


class TestHosttechDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id_prefix(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23/records', without_query=True)
            .expect_query_values('type', 'MX')
            .return_header('Content-Type', 'application/json')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 401)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .result_str(''),
        ])

        assert result['msg'] == 'Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401)'

    def test_auth_error_forbidden(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 403)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Cannot authenticate: Forbidden: you do not have access to this resource (HTTP status 403)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 500)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .result_str(''),
        ])

        assert result['msg'].startswith('Error: GET https://api.ns1.hosttech.eu/api/user/v1/zones?')
        assert 'did not yield JSON data, but HTTP status code 500 with Content-Type' in result['msg']

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': '10 example.com',
            'extra': {
                'comment': '',
            },
        }
        assert result['diff']['before'] == result['diff']['after']

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 3600,
            'value': '1.2.3.6',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42
        assert result['diff']['before'] == {}
        assert result['diff']['before'] == {}

    def test_idempotency_absent_value_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'prefix': '*',
            'type': 'A',
            'ttl': 3600,
            'value': '1.2.3.6',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_absent_type(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_absent_record(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': '1.2.3.6',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42
        assert 'warnings' not in result

    def test_absent_check(self, mocker):
        record = HOSTTECH_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record['name'] + 'example.com',
            'type': record['type'],
            'value': record['ipv4'],
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_absent(self, mocker):
        record = HOSTTECH_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record['name'] + 'example.com',
            'type': record['type'],
            'value': record['ipv4'],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
            FetchUrlCall('DELETE', 204)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/{0}'.format(record['id']))
            .result_str(''),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 42,
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 42,
            'prefix': '',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            '_ansible_diff': True,
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records', without_query=True)
            .expect_query_values('type', 'CAA')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {}
        assert result['diff']['after'] == {
            'prefix': '',
            'type': 'CAA',
            'ttl': 3600,
            'value': '0 issue "letsencrypt.org"',
            'extra': {},
        }

    def test_change_add_one(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '128 issue "letsencrypt.org xxx"',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['comment'], '')
            .expect_json_value(['name'], '')
            .expect_json_value(['flag'], '128')
            .expect_json_value(['tag'], 'issue')
            .expect_json_value(['value'], 'letsencrypt.org xxx')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 133,
                    'type': 'CAA',
                    'name': '',
                    'flag': '128',
                    'tag': 'issue',
                    'value': 'letsencrypt.org xxx',
                    'ttl': 3600,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {}
        assert result['diff']['after'] == {
            'prefix': '',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': '128 issue "letsencrypt.org xxx"',
            'extra': {
                'comment': '',
            },
        }

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'prefix': '',
            'type': 'CAA',
            'ttl': 3600,
            'value': '128 issue "letsencrypt.org"',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['comment'], '')
            .expect_json_value(['name'], '')
            .expect_json_value(['flag'], '128')
            .expect_json_value(['tag'], 'issue')
            .expect_json_value(['value'], 'letsencrypt.org')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 133,
                    'type': 'CAA',
                    'name': '',
                    'flag': '128',
                    'tag': 'issue',
                    'value': 'letsencrypt.org',
                    'ttl': 3600,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_idn_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'prefix': '☺',
            'type': 'CAA',
            'ttl': 3600,
            'value': '128 issue "letsencrypt.org"',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['comment'], '')
            .expect_json_value(['name'], 'xn--74h')
            .expect_json_value(['flag'], '128')
            .expect_json_value(['tag'], 'issue')
            .expect_json_value(['value'], 'letsencrypt.org')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 133,
                    'type': 'CAA',
                    'name': 'xn--74h',
                    'flag': '128',
                    'tag': 'issue',
                    'value': 'letsencrypt.org',
                    'ttl': 3600,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_modify_check(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 300,
            'value': '1.2.3.5',
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_modify(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 300,
            'value': '1.2.3.5',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/126')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 300)
            .expect_json_value(['name'], '*')
            .expect_json_value(['ipv4'], '1.2.3.5')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': '126',
                    'type': 'A',
                    'name': '*',
                    'ipv4': '1.2.3.5',
                    'ttl': 300,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
