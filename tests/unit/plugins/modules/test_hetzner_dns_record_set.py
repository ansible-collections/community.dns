# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from ansible_collections.community.dns.plugins.modules import hetzner_dns_record_set

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa

from .hetzner import (
    HETZNER_JSON_DEFAULT_ENTRIES,
    HETZNER_JSON_ZONE_GET_RESULT,
    HETZNER_JSON_ZONE_LIST_RESULT,
    HETZNER_JSON_ZONE_RECORDS_GET_RESULT,
)


class TestHetznerDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_record_set.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.org')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_id': '23',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json({'error': {'message': 'zone not found', 'code': 404}}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id_prefix(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_id': '23',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '23')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json({'records': [], 'error': {'message': 'zone not found', 'code': 404}}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.org')
            .result_json({'message': 'Invalid authentication credentials'}),
        ])

        assert result['msg'] == (
            'Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401): Invalid authentication credentials'
        )

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.org')
            .result_str(''),
        ])

        assert result['msg'].startswith('Error: GET https://dns.hetzner.com/api/v1/zones?')
        assert 'did not yield JSON data, but HTTP status code 500 with Content-Type' in result['msg']

    def test_conversion_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'TXT',
            'ttl': 3600,
            'value': [
                u'"hellö',
            ],
            'txt_transformation': 'quoted',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['msg'] == (
            'Error while converting DNS values: While processing record from the user: Missing double quotation mark at the end of value'
        )

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'MX',
            'ttl': 3600,
            'value': ['10 example.com'],
        }
        assert result['diff']['before'] == result['diff']['after']

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record': '*.example.com',
            'prefix': '*',
            'type': 'A',
            'ttl': 3600,
            'value': ['1.2.3.5'],
        }
        assert result['diff']['before'] == result['diff']['after']

    def test_idempotency_absent_value_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_idempotency_absent_ttl(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_idempotency_absent_type(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_idempotency_absent_record(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert 'warnings' not in result

    def test_idempotency_absent_record_warn(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert list(result['warnings']) == ["Record already exists with different value. Set on_existing=replace to remove it"]

    def test_idempotency_absent_record_fail(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['msg'] == "Record already exists with different value. Set on_existing=replace to remove it"

    def test_absent(self, mocker):
        record = HETZNER_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': ((record['name'] + '.') if record['name'] != '@' else '') + 'example.com',
            'type': record['type'],
            'ttl': record['ttl'],
            'value': [
                record['value'],
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/{0}'.format(record['id']))
            .result_str(''),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_absent_error(self, mocker):
        record = HETZNER_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': ((record['name'] + '.') if record['name'] != '@' else '') + 'example.com',
            'type': record['type'],
            'ttl': record['ttl'],
            'value': [
                record['value'],
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 500)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/{0}'.format(record['id']))
            .return_header('Content-Type', 'application/json')
            .result_json({'error': {'message': 'Internal Server Error', 'code': 500}}),
        ])

        print(result['msg'])
        assert result['msg'] == (
            'Error: Expected HTTP status 200, 404 for DELETE https://dns.hetzner.com/api/v1/records/125,'
            ' but got HTTP status 500 (Internal Server Error) with error message "Internal Server Error" (error code 500)'
        )

    def test_absent_bulk(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/130')
            .result_str(''),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .result_str(''),
            # Record 132 has been deleted between querying and we trying to delete it
            FetchUrlCall('DELETE', 404)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'record does not exist'}),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_absent_bulk_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/130')
            .result_str(''),
            FetchUrlCall('DELETE', 500)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .return_header('Content-Type', 'application/json')
            .result_json({'error': {'message': 'Internal Server Error', 'code': 500}}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 200, 404 for DELETE https://dns.hetzner.com/api/v1/records/131,'
            ' but got HTTP status 500 (Internal Server Error) with error message "Internal Server Error" (error code 500)'
        )

    def test_absent_other_value(self, mocker):
        record = HETZNER_JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'absent',
            'zone_name': 'example.com',
            'record': ((record['name'] + '.') if record['name'] != '@' else '') + 'example.com',
            'type': record['type'],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/{0}'.format(record['id']))
            .result_str(''),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_id': '42',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_GET_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_id': '42',
            'prefix': '@',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
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
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('POST', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], '128 issue "letsencrypt.org xxx"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': '@',
                    'value': '128 issue "letsencrypt.org xxx"',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('POST', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], '128 issue "letsencrypt.org"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': '@',
                    'value': '128 issue "letsencrypt.org"',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_idn_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('POST', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'CAA')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], 'xn--74h')
            .expect_json_value(['value'], '128 issue "letsencrypt.org"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': 'xn--74h',
                    'value': '128 issue "letsencrypt.org"',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_modify_list_fail(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': None,
            'value': [
                'helium.ns.hetzner.de.',
                'ytterbium.ns.hetzner.com.',
            ],
            'on_existing': 'keep_and_fail',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['msg'] == "Record already exists with different value. Set on_existing=replace to replace it"

    def test_change_modify_list_warn(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'helium.ns.hetzner.de.',
                'ytterbium.ns.hetzner.com.',
            ],
            'on_existing': 'keep_and_warn',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': None,
            'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
        }
        assert result['diff']['after'] == result['diff']['before']
        assert list(result['warnings']) == ["Record already exists with different value. Set on_existing=replace to replace it"]

    def test_change_modify_list_keep(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': None,
            'value': [
                'helium.ns.hetzner.de.',
                'ytterbium.ns.hetzner.com.',
            ],
            'on_existing': 'keep',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert 'warnings' not in result
        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': None,
            'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
        }
        assert result['diff']['after'] == result['diff']['before']

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': None,
            'value': [
                'helium.ns.hetzner.de.',
                'ytterbium.ns.hetzner.com.',
            ],
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .result_str(''),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value_absent(['ttl'])
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'ytterbium.ns.hetzner.com.')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '132',
                    'type': 'NS',
                    'name': '@',
                    'value': 'ytterbium.ns.hetzner.com.',
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': None,
            'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
        }
        assert result['diff']['after'] == {
            'record': 'example.com',
            'prefix': '',
            'type': 'NS',
            'ttl': None,
            'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
        }

    def test_change_modify_txt_unquoted(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'foo.example.com',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär "with quotes" (use \\ to escape)!'],
            'txt_transformation': 'unquoted',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/201')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'TXT')
            .expect_json_value_absent(['ttl'])
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], 'foo')
            .expect_json_value(['value'], u'"bär \\"with quotes\\" (use \\\\ to escape)!"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '201',
                    'type': 'TXT',
                    'name': 'foo',
                    'value': u'"bär \\"with quotes\\" (use \\\\ to escape)!"',
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär "with quotes" (use \\ to escape)'],
        }
        assert result['diff']['after'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär "with quotes" (use \\ to escape)!'],
        }

    def test_change_modify_txt_quoted(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'foo.example.com',
            'type': 'TXT',
            'ttl': None,
            'value': [r'"b\303\244r \"with quotes\" (use \\ to escape)!"'],
            'txt_transformation': 'quoted',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/201')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'TXT')
            .expect_json_value_absent(['ttl'])
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], 'foo')
            .expect_json_value(['value'], u'"bär \\"with quotes\\" (use \\\\ to escape)!"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '201',
                    'type': 'TXT',
                    'name': 'foo',
                    'value': u'"bär \\"with quotes\\" (use \\\\ to escape)!"',
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [r'"b\303\244r \"with quotes\" (use \\ to escape)"'],
        }
        assert result['diff']['after'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [r'"b\303\244r \"with quotes\" (use \\ to escape)!"'],
        }

    def test_change_modify_txt_api(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'foo.example.com',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär " " \\"with " " quotes\\" " (use \\\\ to escape)!"'],
            'txt_transformation': 'api',
            '_ansible_diff': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/201')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'TXT')
            .expect_json_value_absent(['ttl'])
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], 'foo')
            .expect_json_value(['value'], u'bär " " \\"with " " quotes\\" " (use \\\\ to escape)!"')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '201',
                    'type': 'TXT',
                    'name': 'foo',
                    'value': u'bär " " \\"with " " quotes\\" " (use \\\\ to escape)!"',
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär " \\"with quotes\\"" " " "(use \\\\ to escape)"'],
        }
        assert result['diff']['after'] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'type': 'TXT',
            'ttl': None,
            'value': [u'bär " " \\"with " " quotes\\" " (use \\\\ to escape)!"'],
        }

    def test_change_modify_bulk(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '132',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a1',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a2')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '131',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a2',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/130')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a3')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '130',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a3',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('POST', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/bulk')
            .expect_json_value_absent(['records', 0, 'id'])
            .expect_json_value(['records', 0, 'type'], 'NS')
            .expect_json_value(['records', 0, 'ttl'], 10800)
            .expect_json_value(['records', 0, 'zone_id'], '42')
            .expect_json_value(['records', 0, 'name'], '@')
            .expect_json_value(['records', 0, 'value'], 'a4')
            .expect_json_value_absent(['records', 1, 'id'])
            .expect_json_value(['records', 1, 'type'], 'NS')
            .expect_json_value(['records', 1, 'ttl'], 10800)
            .expect_json_value(['records', 1, 'zone_id'], '42')
            .expect_json_value(['records', 1, 'name'], '@')
            .expect_json_value(['records', 1, 'value'], 'a5')
            .expect_json_value_absent(['records', 2, 'id'])
            .expect_json_value(['records', 2, 'type'], 'NS')
            .expect_json_value(['records', 2, 'ttl'], 10800)
            .expect_json_value(['records', 2, 'zone_id'], '42')
            .expect_json_value(['records', 2, 'name'], '@')
            .expect_json_value(['records', 2, 'value'], 'a6')
            .expect_json_value_absent(['records', 3])
            .return_header('Content-Type', 'application/json')
            .result_json({
                'invalid_records': [],
                'valid_records': [],
                'records': [
                    {
                        'id': '300',
                        'type': 'NS',
                        'name': '@',
                        'value': 'a4',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                    {
                        'id': '301',
                        'type': 'NS',
                        'name': '@',
                        'value': 'a5',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                    {
                        'id': '302',
                        'type': 'NS',
                        'name': '@',
                        'value': 'a6',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                ],
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' not in result

    def test_change_modify_bulk_errors(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 500)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 200, 422 for PUT https://dns.hetzner.com/api/v1/records/132,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )

    def test_change_modify_bulk_errors_2(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
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
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a1')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '132',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a1',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a2')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '131',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a2',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/130')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'a3')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '130',
                    'type': 'NS',
                    'name': '@',
                    'value': 'a3',
                    'ttl': 10800,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('POST', 422)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/bulk')
            .expect_json_value_absent(['records', 0, 'id'])
            .expect_json_value(['records', 0, 'type'], 'NS')
            .expect_json_value(['records', 0, 'ttl'], 10800)
            .expect_json_value(['records', 0, 'zone_id'], '42')
            .expect_json_value(['records', 0, 'name'], '@')
            .expect_json_value(['records', 0, 'value'], 'a4')
            .expect_json_value_absent(['records', 1, 'id'])
            .expect_json_value(['records', 1, 'type'], 'NS')
            .expect_json_value(['records', 1, 'ttl'], 10800)
            .expect_json_value(['records', 1, 'zone_id'], '42')
            .expect_json_value(['records', 1, 'name'], '@')
            .expect_json_value(['records', 1, 'value'], 'a5')
            .expect_json_value_absent(['records', 2, 'id'])
            .expect_json_value(['records', 2, 'type'], 'NS')
            .expect_json_value(['records', 2, 'ttl'], 10800)
            .expect_json_value(['records', 2, 'zone_id'], '42')
            .expect_json_value(['records', 2, 'name'], '@')
            .expect_json_value(['records', 2, 'value'], 'a6')
            .expect_json_value_absent(['records', 3])
            .return_header('Content-Type', 'application/json')
            .result_json({
                'invalid_records': [
                    {
                        'type': 'NS',
                        'name': '@',
                        'value': 'a4',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                    {
                        'type': 'NS',
                        'name': '@',
                        'value': 'a5',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                ],
                'valid_records': [
                    {
                        'type': 'NS',
                        'name': '@',
                        'value': 'a6',
                        'ttl': 10800,
                        'zone_id': '42',
                    },
                ],
                'records': [],
                'error': {
                    'message': 'invalid NS record, invalid NS record, ',
                    'code': 422,
                },
            }),
        ])

        assert result['msg'] == (
            'Errors: Creating NS record "a4" with TTL 10800 for zone 42 failed with unknown reason;'
            ' Creating NS record "a5" with TTL 10800 for zone 42 failed with unknown reason'
        )

    def test_change_change_bad(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set, {
            'hetzner_token': 'foo',
            'state': 'present',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.4.5',
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records', without_query=True)
            .expect_query_values('zone_id', '42')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
            FetchUrlCall('PUT', 422)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/125')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'A')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], '1.2.3.4.5')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '',
                    'type': '',
                    'name': '',
                    'value': '',
                    'zone_id': '',
                    'created': '',
                    'modified': '',
                },
                'error': {
                    'message': 'invalid A record',
                    'code': 422,
                }
            }),
        ])

        assert result['msg'] == (
            'Error: The updated A record with value "1.2.3.4.5" and TTL 3600 has not been accepted'
            ' by the server with error message "invalid A record" (error code 422)'
        )
