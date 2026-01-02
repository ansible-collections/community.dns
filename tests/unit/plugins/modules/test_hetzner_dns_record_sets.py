# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa: F401, pylint: disable=unused-import
from ansible_collections.community.dns.plugins.modules import hetzner_dns_record_sets

from .hetzner import (
    HETZNER_JSON_ZONE_GET_RESULT,
    HETZNER_JSON_ZONE_LIST_RESULT,
    HETZNER_JSON_ZONE_RECORDS_GET_RESULT,
    HETZNER_ZONE_NEW_JSON,
    get_hetzner_new_json_records,
)


def mock_sleep(delay):
    pass


class TestHetznerDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_record_sets.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': ""}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 403)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .result_json({'message': ""}),
        ])

        assert result['msg'] == 'Cannot authenticate: Forbidden: you do not have access to this resource (HTTP status 403)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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

    def test_key_collision_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'record': 'test.example.com',
                    'type': 'A',
                    'ignore': True,
                },
                {
                    'prefix': 'test',
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
            ],
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

        assert result['msg'] == 'Found multiple sets for record test.example.com and type A: index #0 and #1'

    def test_conversion_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'TXT',
                    'ttl': 3600,
                    'value': [
                        '"hellö',
                    ],
                },
            ],
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
            .result_json(HETZNER_JSON_ZONE_RECORDS_GET_RESULT),
        ])

        assert result['msg'] == (
            'Error while converting DNS values: While processing record from the user: Missing double quotation mark at the end of value'
        )

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'record_sets': [],
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

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'MX',
                    'ttl': 3600,
                    'value': [
                        '10 example.com',
                    ],
                },
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
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_removal_prune(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'prune': 'true',
            'record_sets': [
                {
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'prefix': '@',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': [],
                },
                {
                    'record': 'example.com',
                    'type': 'MX',
                    'ignore': True,
                },
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ignore': True,
                },
                {
                    'record': 'example.com',
                    'type': 'SOA',
                    'ignore': True,
                },
                {
                    'record': 'foo.example.com',
                    'type': 'TXT',
                    'ttl': None,
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
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
            .expect_url('https://dns.hetzner.com/api/v1/records/{0}'.format(127))
            .result_str(''),
            FetchUrlCall('DELETE', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/{0}'.format(128))
            .result_str(''),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                },
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
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'prefix': '',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                },
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

    def test_change_add_one(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue "letsencrypt.org xxx"',
                    ],
                },
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
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'prefix': '',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue "letsencrypt.org"',
                    ],
                },
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
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'prefix': '☺',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue "letsencrypt.org"',
                    ],
                },
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

    def test_change_add_one_failed(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue "letsencrypt.org xxx"',
                    ],
                },
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
            .result_json({'record': {}, 'error': {'code': 500, 'message': 'Internal Server Error'}}),
        ])

        assert result['msg'] == (
            'Error: POST https://dns.hetzner.com/api/v1/records resulted in API error 500 (Internal Server Error)'
            ' with error message "Internal Server Error" (error code 500)'
        )

    def test_change_add_two_failed(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue "letsencrypt.org xxx"',
                        '128 issuewild "letsencrypt.org"',
                    ],
                },
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
            FetchUrlCall('POST', 422)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/bulk')
            .expect_json_value_absent(['records', 0, 'id'])
            .expect_json_value(['records', 0, 'type'], 'CAA')
            .expect_json_value(['records', 0, 'ttl'], 3600)
            .expect_json_value(['records', 0, 'zone_id'], '42')
            .expect_json_value(['records', 0, 'name'], '@')
            .expect_json_value(['records', 0, 'value'], '128 issue "letsencrypt.org xxx"')
            .expect_json_value_absent(['records', 1, 'id'])
            .expect_json_value(['records', 1, 'type'], 'CAA')
            .expect_json_value(['records', 1, 'ttl'], 3600)
            .expect_json_value(['records', 1, 'zone_id'], '42')
            .expect_json_value(['records', 1, 'name'], '@')
            .expect_json_value(['records', 1, 'value'], '128 issuewild "letsencrypt.org"')
            .expect_json_value_absent(['records', 2])
            .return_header('Content-Type', 'application/json')
            .result_json({
                'invalid_records': [
                    {
                        'type': 'CAA',
                        'name': '@',
                        'value': '128 issue "letsencrypt.org xxx"',
                        'ttl': 3600,
                        'zone_id': '42',
                    },
                    {
                        'type': 'CAA',
                        'name': '@',
                        'value': '128 issuewild "letsencrypt.org"',
                        'ttl': 3600,
                        'zone_id': '42',
                    },
                ],
                'valid_records': [],
                'records': [],
                'error': {
                    'message': 'invalid CAA record, invalid CAA record, ',
                    'code': 422,
                },
            }),
        ])

        assert result['msg'] == (
            'Errors: Creating CAA record "128 issue "letsencrypt.org xxx"" with TTL 3600 for zone 42 failed with unknown reason;'
            ' Creating CAA record "128 issuewild "letsencrypt.org"" with TTL 3600 for zone 42 failed with unknown reason'
        )

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': None,
                    'value': [
                        'helium.ns.hetzner.de.',
                        'ytterbium.ns.hetzner.com.',
                    ],
                },
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
                    'id': '131',
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
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_ttl(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 3600,
                    'value': [
                        'helium.ns.hetzner.de.',
                        'ytterbium.ns.hetzner.com.',
                    ],
                },
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
            .expect_url('https://dns.hetzner.com/api/v1/records/130')
            .result_str(''),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'helium.ns.hetzner.de.')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '130',
                    'type': 'NS',
                    'name': '@',
                    'value': 'ytterbium.ns.hetzner.com.',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value(['type'], 'NS')
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'ytterbium.ns.hetzner.com.')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '131',
                    'type': 'NS',
                    'name': '@',
                    'value': 'ytterbium.ns.hetzner.com.',
                    'ttl': 3600,
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
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': 3600,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }


class TestHetznerDNSRecordNewJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_record_sets.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.org')
            .return_header('Content-Type', 'application/json')
            .result_json({"error": {
                "code": "not_found",
                "message": "Zone not found",
                "details": None,
            }}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_id': 23,
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json({"error": {
                "code": "not_found",
                "message": "Zone not found",
                "details": None,
            }}),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 401)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.org')
            .result_json({"error": {
                "code": "unauthorized",
                "message": "the token you have provided is invalid",
                "details": None,
            }}),
        ])

        assert result['msg'] == 'Cannot authenticate: Unauthorized: the authentication parameters are incorrect (HTTP status 401)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 500)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.org')
            .return_header('Content-Type', 'application/json')
            .result_json({"error": {
                "code": "server_error",
                "message": "something went wrong",
                "details": None,
            }}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 200, 404 for GET https://api.hetzner.cloud/v1/zones/example.org,'
            ' but got HTTP status 500 (Internal Server Error) with error message "something went wrong" (error code server_error)'
        )

    def test_key_collision_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'record': 'test.example.com',
                    'type': 'A',
                    'ignore': True,
                },
                {
                    'prefix': 'test',
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records())
        ])

        assert result['msg'] == 'Found multiple sets for record test.example.com and type A: index #0 and #1'

    def test_conversion_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'TXT',
                    'ttl': 3600,
                    'value': [
                        '"hellö',
                    ],
                },
            ],
            'txt_transformation': 'quoted',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records())
        ])

        assert result['msg'] == (
            'Error while converting DNS values: While processing record from the user: Missing double quotation mark at the end of value'
        )

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_id': '42',
            'record_sets': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records()),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'MX',
                    'ttl': 3600,
                    'value': [
                        '10 example.com',
                    ],
                },
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records()),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_removal_prune(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'prune': 'true',
                'record_sets': [
                    {
                        'prefix': '*',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.5'],
                    },
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.4'],
                    },
                    {
                        'prefix': '@',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                    {
                        'record': 'example.com',
                        'type': 'MX',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ignore': True,
                    },
                    {
                        'record': 'foo.example.com',
                        'type': 'TXT',
                        'ttl': None,
                        'value': [u'bär "with quotes" (use \\ to escape)'],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "delete_rrset",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "delete_rrset",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_removal_prune_already_gone(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'prune': 'true',
                'record_sets': [
                    {
                        'prefix': '*',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.5'],
                    },
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.4'],
                    },
                    {
                        'prefix': '@',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                    {
                        'record': 'example.com',
                        'type': 'MX',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ignore': True,
                    },
                    {
                        'record': 'foo.example.com',
                        'type': 'TXT',
                        'ttl': None,
                        'value': [u'bär "with quotes" (use \\ to escape)'],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('DELETE', 404)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "not_found",
                        "message": "Record not found",
                        "details": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_removal_prune_fail(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'prune': 'true',
                'record_sets': [
                    {
                        'prefix': '*',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.5'],
                    },
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.4'],
                    },
                    {
                        'prefix': '@',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                    {
                        'record': 'example.com',
                        'type': 'MX',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ignore': True,
                    },
                    {
                        'record': 'foo.example.com',
                        'type': 'TXT',
                        'ttl': None,
                        'value': [u'bär "with quotes" (use \\ to escape)'],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "delete_rrset",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "delete_rrset",
                            "status": "error",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": {
                                "code": "server_error",
                                "message": "something went wrong",
                            },
                        },
                    ],
                }),
            ])

        assert result['msg'] in (
            "Errors: Delete record set AAAA *.example.com with TTL=1h and value=['2001:1:2::4']: something went wrong (server_error)",
            # Python 2 compat:
            "Errors: Delete record set AAAA *.example.com with TTL=1h and value=[u'2001:1:2::4']: something went wrong (server_error)",
        )

    def test_removal_prune_fail_2(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'prune': 'true',
                'record_sets': [
                    {
                        'prefix': '*',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.5'],
                    },
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'A',
                        'value': ['1.2.3.4'],
                    },
                    {
                        'prefix': '@',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                    {
                        'record': 'example.com',
                        'type': 'MX',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ignore': True,
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ignore': True,
                    },
                    {
                        'record': 'foo.example.com',
                        'type': 'TXT',
                        'ttl': None,
                        'value': [u'bär "with quotes" (use \\ to escape)'],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('DELETE', 500)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "server_error",
                        "message": "something went wrong",
                        "details": None,
                    },
                }),
            ])

        assert result['msg'] in (
            'Errors: Delete record set AAAA *.example.com with TTL=1h and value=[\'2001:1:2::4\']: Expected HTTP status 201, 404'
            ' for DELETE https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA, but got HTTP status 500 (Internal Server Error)'
            ' with error message "something went wrong" (error code server_error)',
            # Python 2 compat:
            'Errors: Delete record set AAAA *.example.com with TTL=1h and value=[u\'2001:1:2::4\']: Expected HTTP status 201, 404'
            ' for DELETE https://api.hetzner.cloud/v1/zones/42/rrsets/*/AAAA, but got HTTP status 500 (Internal Server Error)'
            ' with error message "something went wrong" (error code server_error)',
        )

    def test_delete(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_delete_already_gone(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 404)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "not_found",
                        "message": "Record not found",
                        "details": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_delete_idempotent(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': 'foo',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
            ])

        assert result['changed'] is False
        assert result['zone_id'] == '42'

    def test_delete_fail(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'ttl': 3600,
                        'type': 'AAAA',
                        'value': [],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('DELETE', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/AAAA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "delete_rrset",
                        "status": "error",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": {
                            "code": "server_error",
                            "message": "something went wrong",
                        },
                    },
                }),
            ])

        assert result['msg'] in (
            "Errors: Delete record set AAAA example.com with TTL=1h and value=['2001:1:2::3']:"
            " Error while deleting record set: something went wrong (server_error)",
            # Python 2 compat:
            "Errors: Delete record set AAAA example.com with TTL=1h and value=[u'2001:1:2::3']:"
            " Error while deleting record set: something went wrong (server_error)",
        )

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                },
            ],
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records()),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_id': '42',
            'record_sets': [
                {
                    'prefix': '',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                },
            ],
            '_ansible_check_mode': True,
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records()),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org xxx"',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org xxx"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/CAA",
                        "name": "@",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org xxx"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_prefix(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/CAA",
                        "name": "@",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_idn_prefix(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '☺',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "xn--74h")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "xn--74h/CAA",
                        "name": "xn--74h",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_failed(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org xxx"',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 500)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org xxx"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({"error": {
                    "code": "server_error",
                    "message": "something went wrong",
                    "details": None,
                }}),
            ])

        assert result['msg'] in (
            'Errors: Create record set CAA example.com with TTL=1h and value=[\'128 issue "letsencrypt.org xxx"\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets,'
            ' but got HTTP status 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
            # Python 2 compat:
            'Errors: Create record set CAA example.com with TTL=1h and value=[u\'128 issue "letsencrypt.org xxx"\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets,'
            ' but got HTTP status 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
        )

    def test_change_add_one_failed_post(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org xxx"',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org xxx"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/CAA",
                        "name": "@",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org xxx"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "error",
                        "progress": 75,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": {
                            "code": "server_error",
                            "message": "something went wrong",
                        },
                    },
                }),
            ])

        assert result['msg'] in (
            'Errors: Create record set CAA example.com with TTL=1h and value=[\'128 issue "letsencrypt.org xxx"\']:'
            ' Error while adding record set: something went wrong (server_error)',
            # Python 2 compat:
            'Errors: Create record set CAA example.com with TTL=1h and value=[u\'128 issue "letsencrypt.org xxx"\']:'
            ' Error while adding record set: something went wrong (server_error)',
        )

    def test_change_add_two(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                    {
                        'prefix': 'foo',
                        'type': 'A',
                        'ttl': 3600,
                        'value': [
                            '1.2.3.4',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/CAA",
                        "name": "@",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "foo")
                .expect_json_value(["type"], "A")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '1.2.3.4')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "foo/A",
                        "name": "foo",
                        "type": "A",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '1.2.3.4',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 2,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:56:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "create_rrset",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "create_rrset",
                            "status": "success",
                            "progress": 50,
                            "started": "2016-01-30T23:56:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_two_fail(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                    {
                        'prefix': 'foo',
                        'type': 'A',
                        'ttl': 3600,
                        'value': [
                            '1.2.3.4',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 500)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "server_error",
                        "message": "something went wrong",
                        "details": None,
                    },
                }),
            ])

        assert result['msg'] in (
            'Errors: Create record set CAA example.com with TTL=1h and value=[\'128 issue "letsencrypt.org"\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets, but got HTTP status'
            ' 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
            # Python 2 compat:
            'Errors: Create record set CAA example.com with TTL=1h and value=[u\'128 issue "letsencrypt.org"\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets, but got HTTP status'
            ' 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
        )

    def test_change_add_two_fail_2(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '',
                        'type': 'CAA',
                        'ttl': 3600,
                        'value': [
                            '128 issue "letsencrypt.org"',
                        ],
                    },
                    {
                        'prefix': 'foo',
                        'type': 'A',
                        'ttl': 3600,
                        'value': [
                            '1.2.3.4',
                        ],
                    },
                ],
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "@")
                .expect_json_value(["type"], "CAA")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '128 issue "letsencrypt.org"')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/CAA",
                        "name": "@",
                        "type": "CAA",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '128 issue "letsencrypt.org"',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 1,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets')
                .expect_json_value(["name"], "foo")
                .expect_json_value(["type"], "A")
                .expect_json_value(["ttl"], 3600)
                .expect_json_value(["records", 0, "value"], '1.2.3.4')
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "foo/A",
                        "name": "foo",
                        "type": "A",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": '1.2.3.4',
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                    "action": {
                        "id": 2,
                        "command": "create_rrset",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:56:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "create_rrset",
                            "status": "error",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": {
                                "code": "server_error",
                                "message": "something went wrong",
                            },
                        },
                        {
                            "id": 2,
                            "command": "create_rrset",
                            "status": "success",
                            "progress": 50,
                            "started": "2016-01-30T23:56:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
            ])

        assert result['msg'] in (
            'Errors: Create record set CAA example.com with TTL=1h and value=[\'128 issue "letsencrypt.org"\']: something went wrong (server_error)',
            # Python 2 compat:
            'Errors: Create record set CAA example.com with TTL=1h and value=[u\'128 issue "letsencrypt.org"\']: something went wrong (server_error)',
        )

    def test_change_modify_list(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/1')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "set_records",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/NS",
                        "name": "@",
                        "type": "NS",
                        "ttl": None,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": "helium.ns.hetzner.de.",
                                "comment": "",
                            },
                            {
                                "value": "ytterbium.ns.hetzner.com.",
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_fail(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 500)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "server_error",
                        "message": "something went wrong",
                        "details": None,
                    },
                }),
            ])

        assert result['msg'] in (
            'Errors: Change record set NS example.com with TTL=default and value=[\'helium.ns.hetzner.de.\', \'ytterbium.ns.hetzner.com.\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records, but got HTTP status 500'
            ' (Internal Server Error) with error message "something went wrong" (error code server_error)',
            # Python 2 compat:
            'Errors: Change record set NS example.com with TTL=default and value=[u\'helium.ns.hetzner.de.\', u\'ytterbium.ns.hetzner.com.\']:'
            ' Expected HTTP status 201 for POST https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records, but got HTTP status 500'
            ' (Internal Server Error) with error message "something went wrong" (error code server_error)',
        )

    def test_change_modify_list_and_ttl(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': 3600,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "running",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": None,
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        "id": "@/NS",
                        "name": "@",
                        "type": "NS",
                        "ttl": 3600,
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                "value": "helium.ns.hetzner.de.",
                                "comment": "",
                            },
                            {
                                "value": "ytterbium.ns.hetzner.com.",
                                "comment": "",
                            },
                        ],
                        "zone": 42,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': 3600,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_and_ttl_suddenly_gone(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': 3600,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "running",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": None,
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 404)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "not_found",
                        "message": "Record not found",
                        "details": None,
                    },
                }),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': 3600,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_and_ttl_multiple(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ttl': 3600,
                        'value': [
                            'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .expect_json_value_absent(["ttl"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "running",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": None,
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_values('name', '@')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records(
                    name='@',
                    update={
                        ('@', 'NS'): {
                            'id': '@/NS',
                            'type': 'NS',
                            'name': '@',
                            "labels": {},
                            "protection": {
                                "change": False,
                            },
                            "records": [
                                {
                                    'value': 'helium.ns.hetzner.de.',
                                    "comment": "",
                                },
                                {
                                    'value': 'ytterbium.ns.hetzner.com.',
                                    "comment": "",
                                },
                            ],
                            "ttl": None,
                            'zone': '42',
                        },
                        ('@', 'SOA'): {
                            'id': '@/SOA',
                            'type': 'SOA',
                            'name': '@',
                            "labels": {},
                            "protection": {
                                "change": False,
                            },
                            "records": [
                                {
                                    'value': 'hydrogen.ns.hetzner.com. dns.hetzner.com. 2025010900 86400 10800 3600000 3600',
                                    "comment": "",
                                },
                            ],
                            "ttl": 3600,
                            'zone': '42',
                        },
                    },
                )),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'type': 'NS',
                    'ttl': None,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_and_ttl_multiple_2(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'prefix': '@',
                        'type': 'A',
                        'ttl': 3600,
                        'value': [
                            '1.1.1.1',
                        ],
                    },
                    {
                        'prefix': '*',
                        'type': 'A',
                        'ttl': 300,
                        'value': [
                            '1.2.3.5',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/A/actions/set_records')
                .expect_json_value(["records", 0, "value"], "1.1.1.1")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value_absent(["records", 1])
                .expect_json_value_absent(["ttl"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/*/A/actions/change_ttl')
                .expect_json_value(["ttl"], 300)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "running",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": None,
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "success",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_values('type', 'A')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records(
                    record_type='A',
                    update={
                        ('@', 'A'): {
                            'id': '@/A',
                            'type': 'A',
                            'name': '@',
                            "labels": {},
                            "protection": {
                                "change": False,
                            },
                            "records": [
                                {
                                    'value': '1.1.1.1',
                                    "comment": "",
                                },
                            ],
                            "ttl": 3600,
                            'zone': '42',
                        },
                        ('*', 'A'): {
                            'id': '*/A',
                            'type': 'A',
                            'name': '*',
                            "labels": {},
                            "protection": {
                                "change": False,
                            },
                            "records": [
                                {
                                    'value': '1.2.3.5',
                                    "comment": "",
                                },
                            ],
                            "ttl": 300,
                            'zone': '42',
                        },
                    },
                )),
            ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.2.3.4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }
        assert result['diff']['after'] == {
            'record_sets': [
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 300,
                    'type': 'A',
                    'value': ['1.2.3.5'],
                },
                {
                    'record': '*.example.com',
                    'prefix': '*',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::4'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'A',
                    'value': ['1.1.1.1'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'AAAA',
                    'value': ['2001:1:2::3'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': 3600,
                    'type': 'MX',
                    'value': ['10 example.com'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'NS',
                    'value': ['helium.ns.hetzner.de.', 'hydrogen.ns.hetzner.com.', 'oxygen.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
                {
                    'record': 'foo.example.com',
                    'prefix': 'foo',
                    'ttl': None,
                    'type': 'TXT',
                    'value': [u'bär "with quotes" (use \\ to escape)'],
                },
            ],
        }

    def test_change_modify_list_and_ttl_multiple_fail(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ttl': 3600,
                        'value': [
                            'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .expect_json_value_absent(["ttl"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 500)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "error": {
                        "code": "server_error",
                        "message": "something went wrong",
                        "details": None,
                    },
                }),
            ])

        assert result['msg'] in (
            'Errors: Change record set SOA example.com with TTL=1h and value=[\'hydrogen.ns.hetzner.com.'
            ' dns.hetzner.com. 2021070900 86400 10800 3600000 3600\']: Expected HTTP status 201 for POST'
            ' https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl, but got HTTP status'
            ' 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
            # Python 2 compat:
            'Errors: Change record set SOA example.com with TTL=1h and value=[u\'hydrogen.ns.hetzner.com.'
            ' dns.hetzner.com. 2021070900 86400 10800 3600000 3600\']: Expected HTTP status 201 for POST'
            ' https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl, but got HTTP status'
            ' 500 (Internal Server Error) with error message "something went wrong" (error code server_error)',
        )

    def test_change_modify_list_and_ttl_multiple_fail_2(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ttl': 3600,
                        'value': [
                            'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .expect_json_value_absent(["ttl"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "success",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "running",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": None,
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": None,
                        },
                    ],
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions/2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "error",
                        "progress": 100,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": "2026-01-30T23:55:00Z",
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": {
                            "code": "server_error",
                            "message": "something went wrong",
                        },
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "rrset": {
                        'id': '@/SOA',
                        'type': 'SOA',
                        'name': '@',
                        "labels": {},
                        "protection": {
                            "change": False,
                        },
                        "records": [
                            {
                                'value': 'hydrogen.ns.hetzner.com. dns.hetzner.com. 2025010900 86400 10800 3600000 3600',
                                "comment": "",
                            },
                        ],
                        "ttl": 3600,
                        'zone': '42',
                    },
                }),
            ])

        assert result['msg'] in (
            "Errors: Change record set NS example.com with TTL=default and value=['helium.ns.hetzner.de.',"
            " 'ytterbium.ns.hetzner.com.']: something went wrong (server_error)",
            # Python 2 compat:
            "Errors: Change record set NS example.com with TTL=default and value=[u'helium.ns.hetzner.de.',"
            " u'ytterbium.ns.hetzner.com.']: something went wrong (server_error)",
        )

    def test_change_modify_list_and_ttl_multiple_fail_3(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
                'hetzner_api_token': 'foo',
                'zone_name': 'example.com',
                'record_sets': [
                    {
                        'record': 'example.com',
                        'type': 'NS',
                        'ttl': None,
                        'value': [
                            'helium.ns.hetzner.de.',
                            'ytterbium.ns.hetzner.com.',
                        ],
                    },
                    {
                        'record': 'example.com',
                        'type': 'SOA',
                        'ttl': 3600,
                        'value': [
                            'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600',
                        ],
                    },
                ],
                '_ansible_diff': True,
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
                .return_header('Content-Type', 'application/json')
                .result_json(HETZNER_ZONE_NEW_JSON),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
                .expect_query_absent('name')
                .expect_query_absent('type')
                .expect_query_values('page', '1')
                .expect_query_values('per_page', '100')
                .return_header('Content-Type', 'application/json')
                .result_json(get_hetzner_new_json_records()),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/NS/actions/set_records')
                .expect_json_value(["records", 0, "value"], "helium.ns.hetzner.de.")
                .expect_json_value(["records", 0, "comment"], None)
                .expect_json_value(["records", 1, "value"], "ytterbium.ns.hetzner.com.")
                .expect_json_value(["records", 1, "comment"], None)
                .expect_json_value_absent(["records", 2])
                .expect_json_value_absent(["ttl"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 2,
                        "command": "set_records",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('POST', 201)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets/@/SOA/actions/change_ttl')
                .expect_json_value(["ttl"], 3600)
                .expect_json_value_absent(["records"])
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "action": {
                        "id": 1,
                        "command": "change_rrset_ttl",
                        "status": "running",
                        "progress": 50,
                        "started": "2016-01-30T23:55:00Z",
                        "finished": None,
                        "resources": [
                            {
                                "id": 42,
                                "type": "zone",
                            },
                        ],
                        "error": None,
                    },
                }),
                FetchUrlCall('GET', 200)
                .expect_header('accept', 'application/json')
                .expect_header('Authorization', 'Bearer foo')
                .expect_url('https://api.hetzner.cloud/v1/actions?id=1&id=2')
                .return_header('Content-Type', 'application/json')
                .result_json({
                    "actions": [
                        {
                            "id": 1,
                            "command": "change_rrset_ttl",
                            "status": "error",
                            "progress": 100,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": {
                                "code": "server_error",
                                "message": "something went wrong",
                            },
                        },
                        {
                            "id": 2,
                            "command": "set_records",
                            "status": "error",
                            "progress": 75,
                            "started": "2016-01-30T23:55:00Z",
                            "finished": "2026-01-30T23:55:00Z",
                            "resources": [
                                {
                                    "id": 42,
                                    "type": "zone",
                                },
                            ],
                            "error": {
                                "code": "server_error",
                                "message": "something went wrong",
                            },
                        },
                    ],
                }),
            ])

        assert result['msg'] in (
            "Errors: Change record set NS example.com with TTL=default and value=['helium.ns.hetzner.de.',"
            " 'ytterbium.ns.hetzner.com.']: something went wrong (server_error); Change record set SOA example.com"
            " with TTL=1h and value=['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600']:"
            " something went wrong (server_error)",
            # Python 2 compat:
            "Errors: Change record set NS example.com with TTL=default and value=[u'helium.ns.hetzner.de.',"
            " u'ytterbium.ns.hetzner.com.']: something went wrong (server_error); Change record set SOA example.com"
            " with TTL=1h and value=[u'hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600']:"
            " something went wrong (server_error)",
        )

    def test_wrong_tpye(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_record_sets, {
            'hetzner_api_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'DANE',
                    'ttl': 3600,
                    'value': ['...'],
                },
            ],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HETZNER_ZONE_NEW_JSON),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('Authorization', 'Bearer foo')
            .expect_url('https://api.hetzner.cloud/v1/zones/42/rrsets', without_query=True)
            .expect_query_absent('name')
            .expect_query_absent('type')
            .expect_query_values('page', '1')
            .expect_query_values('per_page', '100')
            .return_header('Content-Type', 'application/json')
            .result_json(get_hetzner_new_json_records()),
        ])

        assert result['msg'] == "Found invalid record type DANE at index #0"
