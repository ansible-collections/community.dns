# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa: F401, pylint: disable=unused-import
import pytest
from ansible_collections.community.dns.plugins.modules import hosttech_dns_record_sets
from ansible_collections.community.internal_test_tools.tests.unit.utils.fetch_url_module_framework import (
    BaseTestModule,
    FetchUrlCall,
)

from .hosttech import (
    HOSTTECH_JSON_ZONE_GET_RESULT,
    HOSTTECH_JSON_ZONE_LIST_RESULT,
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
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_sets.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.org',
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_id': 23,
            'record_sets': [],
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
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'prefix': '',
                    'type': 'A',
                    'value': '1.2.3.4',
                },
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

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                }
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
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'foo.example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        '0 issue "letsencrypt.org"',
                    ],
                }
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

    def test_change_modify_list(self, mocker):
        del_entry = (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None)
        update_entry = (131, 42, 'NS', '', 'ns4.hostserv.eu', 10800, None, None)
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns4.hostserv.eu',
                    ],
                },
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'ttl': 10800,
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }


class TestHosttechDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_sets.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'record_sets': [],
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

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'record_sets': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record_sets': [],
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

    def test_key_collision_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['msg'] == 'Found multiple sets for record test.example.com and type A: index #0 and #1'

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 42,
            'record_sets': [],
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

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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

    def test_removal_prune(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/{0}'.format(127))
            .result_str(''),
            FetchUrlCall('DELETE', 204)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/{0}'.format(128))
            .result_str(''),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'ttl': 10800,
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
                },
            ],
        }

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_failed(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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
            .expect_json_value(['name'], '')
            .expect_json_value(['flag'], '128')
            .expect_json_value(['tag'], 'issue')
            .expect_json_value(['value'], 'letsencrypt.org xxx')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'Internal Server Error'}),
        ])

        assert result['msg'] == (
            'Error: Expected HTTP status 201 for POST https://api.ns1.hosttech.eu/api/user/v1/zones/42/records,'
            ' but got HTTP status 500 (Internal Server Error) with message "Internal Server Error"'
        )

    def test_change_add_one(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
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

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns4.hostserv.eu',
                    ],
                },
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'ttl': 10800,
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }

    def test_change_modify_list_nodelete(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns2.hostserv.eu',
                    ],
                },
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
            FetchUrlCall('DELETE', 404)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/130')
            .return_header('Content-Type', 'application/json')
            .result_json({'message': 'record does not exist'}),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'ttl': 10800,
                    'value': ['ns2.hostserv.eu', 'ns1.hostserv.eu'],
                },
            ],
        }

    def test_change_modify_list_ttl(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_sets, {
            'hosttech_token': 'foo',
            'zone_name': 'example.com',
            'record_sets': [
                {
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 3600,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns4.hostserv.eu',
                    ],
                },
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
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/132')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 3600)
            .expect_json_value(['comment'], '')
            .expect_json_value(['ownername'], '')
            .expect_json_value(['targetname'], 'ns1.hostserv.eu')
            .return_header('Content-Type', 'application/json')
            .result_json({
                'data': {
                    'id': 130,
                    'type': 'NS',
                    'ownername': '',
                    'targetname': 'ns4.hostserv.eu',
                    'ttl': 3600,
                    'comment': '',
                },
            }),
            FetchUrlCall('PUT', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/131')
            .expect_json_value_absent(['id'])
            .expect_json_value_absent(['type'])
            .expect_json_value(['ttl'], 3600)
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }
