# -*- coding: utf-8 -*-
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

from ansible_collections.community.dns.plugins.modules import hosttech_dns_record_info

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa

from .hosttech import (
    expect_wsdl_authentication,
    expect_wsdl_value,
    validate_wsdl_call,
    HOSTTECH_WSDL_DEFAULT_ZONE_RESULT,
    HOSTTECH_WSDL_ZONE_NOT_FOUND,
    HOSTTECH_JSON_ZONE_GET_RESULT,
    HOSTTECH_JSON_ZONE_LIST_RESULT,
)

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False


def mock_sleep(delay):
    pass


@pytest.mark.skipif(not HAS_LXML_ETREE, reason="Need lxml.etree for WSDL tests")
class TestHosttechDNSRecordInfoWSDL(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'A',
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

    def test_get_single(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
            'record': 'example.com',
            'type': 'A',
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
        assert len(result['records']) == 1
        assert result['records'][0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.4',
            'extra': {
                'comment': '',
            },
        }

    def test_get_all_for_one_record(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'what': 'all_types_for_record',
            'zone_id': 42,
            'record': '*.example.com',
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
        assert len(result['records']) == 2
        assert result['records'][0] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.5',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::4',
            'extra': {
                'comment': '',
            },
        }

    def test_get_all(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'what': 'all_records',
            'zone_name': 'example.com.',
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
        assert len(result['records']) == 8
        assert result['records'][0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.4',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.5',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][2] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::3',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][3] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::4',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][4] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'MX',
            'value': '10 example.com',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][5] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns3.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][6] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns2.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][7] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns1.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }


class TestHosttechDNSRecordInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'A',
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

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'record': 'example.org',
            'type': 'A',
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
        result = self.run_module_failed(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
            'record': 'example.org',
            'type': 'A',
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

    def test_too_many_retries(self, mocker):
        sleep_values = [5, 10, 1, 1, 1, 60, 10, 1, 10, 3.1415]

        def sleep_check(delay):
            expected = sleep_values.pop(0)
            assert delay == expected

        with patch('time.sleep', sleep_check):
            result = self.run_module_failed(mocker, hosttech_dns_record_info, {
                'hosttech_token': 'foo',
                'zone_name': 'example.com',
                'record': 'example.com',
                'type': 'A',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('authorization', 'Bearer foo')
                .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
                .expect_query_values('query', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('authorization', 'Bearer foo')
                .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
                .expect_query_values('query', 'example.com')
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

    def test_get_single(self, mocker):
        with patch('time.sleep', mock_sleep):
            result = self.run_module_success(mocker, hosttech_dns_record_info, {
                'hosttech_token': 'foo',
                'zone_name': 'example.com',
                'record': 'example.com',
                'type': 'A',
                '_ansible_remote_tmp': '/tmp/tmp',
                '_ansible_keep_remote_files': True,
            }, [
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('authorization', 'Bearer foo')
                .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
                .expect_query_values('query', 'example.com')
                .return_header('Retry-After', '5')
                .result_str(''),
                FetchUrlCall('GET', 429)
                .expect_header('accept', 'application/json')
                .expect_header('authorization', 'Bearer foo')
                .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
                .expect_query_values('query', 'example.com')
                .return_header('Retry-After', '10')
                .result_str(''),
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
        assert len(result['records']) == 1
        assert result['records'][0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.4',
            'extra': {
                'comment': '',
            },
        }

    def test_get_single_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.com',
            'prefix': '*',
            'type': 'A',
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
        assert len(result['records']) == 1
        assert result['records'][0] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.5',
            'extra': {
                'comment': '',
            },
        }

    def test_get_all_for_one_record(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'what': 'all_types_for_record',
            'zone_name': 'example.com',
            'record': '*.example.com',
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
        assert len(result['records']) == 2
        assert result['records'][0] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.5',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::4',
            'extra': {
                'comment': '',
            },
        }

    def test_get_all_for_one_record_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'what': 'all_types_for_record',
            'zone_name': 'example.com.',
            'prefix': '',
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
        assert len(result['records']) == 6
        assert result['records'][0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.4',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][1] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::3',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][2] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'MX',
            'value': '10 example.com',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][3] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns3.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][4] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns2.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][5] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns1.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }

    def test_get_all(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record_info, {
            'hosttech_token': 'foo',
            'what': 'all_records',
            'zone_id': 42,
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
        assert len(result['records']) == 8
        assert result['records'][0] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.4',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][1] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'A',
            'value': '1.2.3.5',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][2] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::3',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][3] == {
            'record': '*.example.com',
            'prefix': '*',
            'ttl': 3600,
            'type': 'AAAA',
            'value': '2001:1:2::4',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][4] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 3600,
            'type': 'MX',
            'value': '10 example.com',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][5] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns3.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][6] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns2.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
        assert result['records'][7] == {
            'record': 'example.com',
            'prefix': '',
            'ttl': 10800,
            'type': 'NS',
            'value': 'ns1.hostserv.eu',
            'extra': {
                'comment': '',
            },
        }
