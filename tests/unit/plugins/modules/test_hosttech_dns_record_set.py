# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa: F401, pylint: disable=unused-import
import pytest
from ansible_collections.community.dns.plugins.modules import hosttech_dns_record_set
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    extract_warnings_texts,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from .hosttech import (
    HOSTTECH_JSON_DEFAULT_ENTRIES,
    HOSTTECH_JSON_ZONE_GET_RESULT,
    HOSTTECH_JSON_ZONE_LIST_RESULT,
    HOSTTECH_JSON_ZONE_RECORDS_GET_RESULT,
    HOSTTECH_WSDL_DEFAULT_ENTRIES,
    HOSTTECH_WSDL_DEFAULT_ZONE_RESULT,
    HOSTTECH_WSDL_ZONE_NOT_FOUND,
    create_wsdl_add_result,
    create_wsdl_del_result,
    create_wsdl_update_result,
    expect_wsdl_authentication,
    expect_wsdl_value,
    validate_wsdl_add_request,
    validate_wsdl_call,
    validate_wsdl_del_request,
    validate_wsdl_update_request,
)


try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:  # pragma: no cover
    HAS_LXML_ETREE = False  # pragma: no cover


@pytest.mark.skipif(not HAS_LXML_ETREE, reason="Need lxml.etree for WSDL tests")
class TestHosttechDNSRecordWSDL(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_set.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_id': 23,
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep',
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

    def test_idempotency_absent_ttl(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 1800,
            'value': [
                '1.2.3.5',
            ],
            'on_existing': 'keep',
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_id': 42,
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
            'on_existing': 'keep',
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep',
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record[3] + 'example.com',
            'type': record[2],
            'ttl': record[5],
            'value': [
                record[4],
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'foo.example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
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

    def test_change_modify_list_fail(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            'on_existing': 'keep_and_fail',
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

        assert result['msg'] == "Record already exists with different value. Set on_existing=replace to replace it"

    def test_change_modify_list(self, mocker):
        del_entry = (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None)
        update_entry = (131, 42, 'NS', '', 'ns4.hostserv.eu', 10800, None, None)
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            '_ansible_diff': True,
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
                validate_wsdl_del_request(del_entry),
            ]))
            .result_str(create_wsdl_del_result(True)),
            FetchUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_update_request(update_entry),
            ]))
            .result_str(create_wsdl_update_result(update_entry)),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert result['diff']['after'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
        }


class TestHosttechDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_set.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': ''}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id_prefix(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23/records', without_query=True)
            .expect_query_values('type', 'MX')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': ''}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 403)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/23')
            .result_json({'message': ''}),
        ])

        assert result['msg'] == 'Cannot authenticate: Forbidden: you do not have access to this resource (HTTP status 403)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'MX',
            'ttl': 3600,
            'value': [
                '10 example.com',
            ],
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
            'value': ['10 example.com'],
        }
        assert result['diff']['before'] == result['diff']['after']

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep',
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
            'record': '*.example.com',
            'prefix': '*',
            'type': 'A',
            'ttl': 3600,
            'value': ['1.2.3.5'],
        }
        assert result['diff']['before'] == result['diff']['after']

    def test_idempotency_absent_value_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'prefix': '*',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep',
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

    def test_idempotency_absent_ttl(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 1800,
            'value': [
                '1.2.3.5',
            ],
            'on_existing': 'keep',
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
            'on_existing': 'keep',
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep',
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
        assert extract_warnings_texts(result) == []  # pylint: disable=use-implicit-booleaness-not-comparison

    def test_idempotency_absent_record_warn(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep_and_warn',
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
        assert extract_warnings_texts(result) == ["Record already exists with different value. Set on_existing=replace to remove it"]

    def test_idempotency_absent_record_fail(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
            ],
            'on_existing': 'keep_and_fail',
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

        assert result['msg'] == "Record already exists with different value. Set on_existing=replace to remove it"

    def test_absent(self, mocker):
        record = HOSTTECH_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record['name'] + 'example.com',
            'type': record['type'],
            'ttl': record['ttl'],
            'value': [
                record['ipv4'],
            ],
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

    def test_absent_bulk(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'value': [],
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .result_str(''),
            FetchUrlCall('DELETE', 204)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .result_str(''),
            # Record 132 has been deleted between querying and we trying to delete it
            FetchUrlCall('DELETE', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'record does not exist'}),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_absent_bulk_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'value': [],
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .result_str(''),
            FetchUrlCall('DELETE', 500)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 204, 404 for DELETE https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )

    def test_absent_other_value(self, mocker):
        record = HOSTTECH_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': record['name'] + 'example.com',
            'type': record['type'],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 42,
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_id': 42,
            'prefix': '',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '0 issue "letsencrypt.org"',
            ],
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
            'value': ['0 issue "letsencrypt.org"'],
        }

    def test_change_add_one(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '128 issue "letsencrypt.org xxx"',
            ],
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

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'prefix': '',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '128 issue "letsencrypt.org"',
            ],
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
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'prefix': '☺',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '128 issue "letsencrypt.org"',
            ],
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

    def test_change_add_one_fail(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'prefix': '☺',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '128 issue "letsencrypt.org"',
            ],
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
            FetchUrlCall('POST', 500)
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
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 201 for POST https://api.ns1.hosttech.eu/api/user/v1/zones/42/records,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )

    def test_change_modify_list_fail(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            'on_existing': 'keep_and_fail',
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

        assert result['msg'] == "Record already exists with different value. Set on_existing=replace to replace it"

    def test_change_modify_list_warn(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            'on_existing': 'keep_and_warn',
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
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert result['diff']['after'] == result['diff']['before']
        assert extract_warnings_texts(result) == ["Record already exists with different value. Set on_existing=replace to replace it"]

    def test_change_modify_list_keep(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            'on_existing': 'keep',
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

        assert extract_warnings_texts(result) == []  # pylint: disable=use-implicit-booleaness-not-comparison
        assert result['changed'] is False
        assert result['zone_id'] == 42
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert result['diff']['after'] == result['diff']['before']

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
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
            FetchUrlCall('DELETE', 204)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .result_str(''),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'ns4.hostserv.eu')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 131,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'ns4.hostserv.eu',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert result['diff']['after'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
        }

    def test_change_modify_bulk(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'a1',
                'a2',
                'a3',
                'a4',
                'a5',
                'a6',
            ],
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 132,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a1',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a2')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 131,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a2',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a3')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 130,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a3',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a4')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 300,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a4',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a5')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 301,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a5',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('POST', 201)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a6')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 302,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a6',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
        assert 'diff' not in result

    def test_change_modify_bulk_errors_update(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'a1',
                'a2',
                'a3',
                'a4',
                'a5',
                'a6',
            ],
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
            FetchUrlCall('PUT', 500)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 200 for PUT https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )

    def test_change_modify_bulk_errors_create(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_set, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'a1',
                'a2',
                'a3',
                'a4',
                'a5',
                'a6',
            ],
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 132,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a1',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a2')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 131,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a2',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a3')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 130,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'a3',
                    'ttl': 10800,
                    'comment': '',
                },
            }),
            FetchUrlCall('POST', 500)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'a4')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 201 for POST https://api.ns1.hosttech.eu/api/user/v1/zones/42/records,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )
