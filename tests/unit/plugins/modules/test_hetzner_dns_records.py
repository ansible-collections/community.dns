# (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch

from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    set_module_args,
    ModuleTestCase,
    AnsibleExitJson,
    AnsibleFailJson,
)

from ansible_collections.community.dns.plugins.modules import hetzner_dns_records

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.wsdl
import ansible_collections.community.dns.plugins.module_utils.json_api_helper

from .hetzner import (
    HETZNER_JSON_ZONE_GET_RESULT,
    HETZNER_JSON_ZONE_LIST_RESULT,
    HETZNER_JSON_ZONE_RECORDS_GET_RESULT,
)


class TestHetznerDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_records.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.json_api_helper.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.org',
            'records': [],
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
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'records': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .return_header('Content-Type', 'application/json')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.org',
            'records': [],
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
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': 23,
            'records': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 403)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Cannot authenticate: Forbidden: you do not have access to this resource (HTTP status 403)'

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.org',
            'records': [],
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
        result = self.run_module_failed(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'records': [
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

        assert result['msg'] == 'Found multiple entries for record test.example.com and type A: index #0 and #1'

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'records': [],
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
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
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
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'prune': 'true',
            'records': [
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
                    'prefix': '',
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
            'records': [
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
            ],
        }
        assert result['diff']['after'] == {
            'records': [
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
            ],
        }

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'records': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        'test',
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
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            'records': [
                {
                    'prefix': '',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        'test',
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
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue letsencrypt.org xxx',
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
            .expect_json_value(['value'], '128 issue letsencrypt.org xxx')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': '@',
                    'value': '128 issue letsencrypt.org xxx',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
                {
                    'prefix': '',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue letsencrypt.org',
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
            .expect_json_value(['value'], '128 issue letsencrypt.org')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': '@',
                    'value': '128 issue letsencrypt.org',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_add_one_idn_prefix(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
                {
                    'prefix': '☺',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '128 issue letsencrypt.org',
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
            .expect_json_value(['value'], '128 issue letsencrypt.org')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '133',
                    'type': 'CAA',
                    'name': 'xn--74h',
                    'value': '128 issue letsencrypt.org',
                    'ttl': 3600,
                    'zone_id': '42',
                },
            }),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == '42'

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
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
            .expect_json_value(['ttl'], 10800)
            .expect_json_value(['zone_id'], '42')
            .expect_json_value(['name'], '@')
            .expect_json_value(['value'], 'helium.ns.hetzner.de.')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '132',
                    'type': 'NS',
                    'name': '@',
                    'value': 'helium.ns.hetzner.de.',
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
            .expect_json_value(['value'], 'ytterbium.ns.hetzner.com.')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'record': {
                    'id': '131',
                    'type': 'NS',
                    'name': '@',
                    'value': 'ytterbium.ns.hetzner.com.',
                    'ttl': 10800,
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
            'records': [
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
            ],
        }
        assert result['diff']['after'] == {
            'records': [
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
                    'ttl': 10800,
                    'value': ['helium.ns.hetzner.de.', 'ytterbium.ns.hetzner.com.'],
                },
                {
                    'record': 'example.com',
                    'prefix': '',
                    'ttl': None,
                    'type': 'SOA',
                    'value': ['hydrogen.ns.hetzner.com. dns.hetzner.com. 2021070900 86400 10800 3600000 3600'],
                },
            ],
        }

    def test_change_modify_list_ttl(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_records, {
            'hetzner_token': 'foo',
            'zone': 'example.com',
            'records': [
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
            'records': [
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
            ],
        }
        assert result['diff']['after'] == {
            'records': [
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
            ],
        }
