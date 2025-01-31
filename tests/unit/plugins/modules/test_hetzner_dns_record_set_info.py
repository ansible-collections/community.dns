# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa: F401, pylint: disable=unused-import
from ansible_collections.community.dns.plugins.modules import (
    hetzner_dns_record_set_info,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from .hetzner import (
    HETZNER_JSON_ZONE_GET_RESULT,
    HETZNER_JSON_ZONE_LIST_RESULT,
    HETZNER_JSON_ZONE_RECORDS_GET_RESULT,
)


def mock_sleep(delay):
    pass


class TestHetznerDNSRecordSetInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_record_set_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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
        result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'A',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': ''}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 401)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.org')
            .result_str(''),
        ])

        assert result['msg'] == 'Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401)'

    def test_auth_error_forbidden(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'A',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 403)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .result_json({'message': ''}),
        ])

        assert result['msg'] == 'Cannot authenticate: Forbidden: you do not have access to this resource (HTTP status 403)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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

    def test_too_many_retries(self, mocker):
        sleep_values = [5, 10, 1, 1, 1, 60, 10, 1, 10, 3.1415]

        def sleep_check(delay):
            expected = sleep_values.pop(0)
            assert delay == expected

        with patch('time.sleep', sleep_check):
            result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'record': 'example.com',
                'type': 'A',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '1')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '0')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '-1')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '61')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', 'foo')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '0.9')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '3.1415')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .return_header('Retry-After', '42')
                .result_str(''),
            ])
        print(sleep_values)
        assert result['msg'] == 'Error: Stopping after 10 failed retries with 429 Too Many Attempts'
        assert len(sleep_values) == 0

    def test_conversion_error(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'record': 'example.com',
                'type': 'TXT',
                'txt_transformation': 'quoted',
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
                .result_json({'records': [
                    {
                        'id': '201',
                        'type': 'TXT',
                        'name': '@',
                        'value': u'"hellö',
                        'zone_id': '42',
                        'created': '2021-07-09T11:18:37Z',
                        'modified': '2021-07-09T11:18:37Z',
                    },
                ]}),
            ])

        assert result['msg'] == (
            'Error while converting DNS values: While processing record from API: Missing double quotation mark at the end of value'
        )

    def test_get_single(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'record': 'example.com',
                'type': 'A',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
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
        assert 'set' in result
        assert result['set']['record'] == 'example.com'
        assert result['set']['prefix'] == ''
        assert result['set']['ttl'] == 3600
        assert result['set']['type'] == 'A'
        assert result['set']['value'] == ['1.2.3.4']
        assert 'sets' not in result

    def test_get_single_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'prefix': '*',
            'type': 'A',
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
        assert 'set' in result
        assert result['set']['record'] == '*.example.com'
        assert result['set']['prefix'] == '*'
        assert result['set']['ttl'] == 3600
        assert result['set']['type'] == 'A'
        assert result['set']['value'] == ['1.2.3.5']
        assert 'sets' not in result

    def test_get_all_for_one_record(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'what': 'all_types_for_record',
            'zone_name': 'example.com',
            'record': '*.example.com',
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
        assert 'set' not in result
        assert 'sets' in result
        sets = result['sets']
        assert len(sets) == 2
        assert sets[0] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.5'],
        }
        assert sets[1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::4'],
        }

    def test_get_all_for_one_record_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'what': 'all_types_for_record',
            'zone_name': 'example.com.',
            'prefix': '@',
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
        assert 'set' not in result
        assert 'sets' in result
        sets = result['sets']
        assert len(sets) == 5
        assert sets[0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.4'],
        }
        assert sets[1] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::3'],
        }
        assert sets[2] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'MX',
            'value': ['10 example.com'],
        }
        assert sets[3] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': None,
            'type': 'NS',
            'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
        }
        assert sets[4] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': None,
            'type': 'SOA',
            'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
        }

    def test_get_all(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
            'hetzner_token': 'foo',
            'what': 'all_records',
            'zone_id': '42',
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
        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert 'set' not in result
        assert 'sets' in result
        sets = result['sets']
        assert len(sets) == 8
        assert sets[0] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.5'],
        }
        assert sets[1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::4'],
        }
        assert sets[2] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.4'],
        }
        assert sets[3] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::3'],
        }
        assert sets[4] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'MX',
            'value': ['10 example.com'],
        }
        assert sets[5] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': None,
            'type': 'NS',
            'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
        }
        assert sets[6] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': None,
            'type': 'SOA',
            'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
        }
        assert sets[7] == {
            'record': 'foo.example.com',
            'prefix': 'foo',
            'ttl': None,
            'type': 'TXT',
            'value': [u'bär "with quotes" (use \\ to escape)'],
        }

    def test_get_single_txt_api(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'prefix': 'foo',
                'type': 'TXT',
                'txt_transformation': 'api',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
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
        assert 'set' in result
        assert result['set']['record'] == 'foo.example.com'
        assert result['set']['prefix'] == 'foo'
        assert result['set']['ttl'] is None
        assert result['set']['type'] == 'TXT'
        assert result['set']['value'] == [u'bär " \\"with quotes\\"" " " "(use \\\\ to escape)"']
        assert 'sets' not in result

    def test_get_single_txt_quoted(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'prefix': 'foo',
                'type': 'TXT',
                'txt_transformation': 'quoted',
                'txt_character_encoding': 'decimal',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
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
        assert 'set' in result
        assert result['set']['record'] == 'foo.example.com'
        assert result['set']['prefix'] == 'foo'
        assert result['set']['ttl'] is None
        assert result['set']['type'] == 'TXT'
        assert result['set']['value'] == [u'"b\\195\\164r \\"with quotes\\" (use \\\\ to escape)"']
        assert 'sets' not in result

    def test_get_single_txt_quoted_octal(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_set_info, {
                'hetzner_token': 'foo',
                'zone_name': 'example.com',
                'prefix': 'foo',
                'type': 'TXT',
                'txt_transformation': 'quoted',
                'txt_character_encoding': 'octal',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('auth-api-token', 'foo')
                .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
                .expect_query_values('name', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
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
        assert 'set' in result
        assert result['set']['record'] == 'foo.example.com'
        assert result['set']['prefix'] == 'foo'
        assert result['set']['ttl'] is None
        assert result['set']['type'] == 'TXT'
        assert result['set']['value'] == [u'"b\\303\\244r \\"with quotes\\" (use \\\\ to escape)"']
        assert 'sets' not in result
