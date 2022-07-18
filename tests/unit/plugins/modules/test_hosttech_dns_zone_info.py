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

from ansible_collections.community.dns.plugins.modules import hosttech_dns_zone_info

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa

from .hosttech import (
    expect_wsdl_authentication,
    expect_wsdl_value,
    validate_wsdl_call,
    HOSTTECH_WSDL_DEFAULT_ZONE_RESULT,
    HOSTTECH_WSDL_ZONE_NOT_FOUND,
    HOSTTECH_JSON_ZONE_GET_RESULT,
    HOSTTECH_JSON_ZONE_2_GET_RESULT,
    HOSTTECH_JSON_ZONE_LIST_RESULT,
)

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False


@pytest.mark.skipif(not HAS_LXML_ETREE, reason="Need lxml.etree for WSDL tests")
class TestHosttechDNSZoneInfoWSDL(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_zone_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.org',
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
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_id': 23,
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

    def test_get(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_zone_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_name': 'example.com',
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
        assert result['zone_name'] == 'example.com'

    def test_get_id(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_zone_info, {
            'hosttech_username': 'foo',
            'hosttech_password': 'bar',
            'zone_id': '42',
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
        assert result['zone_name'] == 'example.com'
        assert result['zone_info'] == {
            'email': 'dns@hosttech.eu',
            'ttl': 10800,
        }


class TestHosttechDNSZoneInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_zone_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
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
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_id': 23,
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
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
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
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_id': 23,
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
        result = self.run_module_failed(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.org',
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

    def test_get(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_name': 'example.com',
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
        assert result['zone_name'] == 'example.com'
        assert result['zone_info'] == {
            'email': 'test@example.com',
            'ttl': 10800,
            'dnssec': False,
            'dnssec_email': None,
            'ds_records': None,
        }

    def test_get_id(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
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
        assert result['zone_name'] == 'example.com'
        assert result['zone_info'] == {
            'email': 'test@example.com',
            'ttl': 10800,
            'dnssec': False,
            'dnssec_email': None,
            'ds_records': None,
        }

    def test_get_dnssec(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_zone_info, {
            'hosttech_token': 'foo',
            'zone_name': 'foo.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'foo.com')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/43')
            .return_header('Content-Type', 'application/json')
            .result_json(HOSTTECH_JSON_ZONE_2_GET_RESULT),
        ])
        assert result['changed'] is False
        assert result['zone_id'] == 43
        assert result['zone_name'] == 'foo.com'
        assert result['zone_info'] == {
            'email': 'test@foo.com',
            'ttl': 10800,
            'dnssec': True,
            'dnssec_email': 'test@foo.com',
            'ds_records': [
                {
                    'key_tag': 12345,
                    'algorithm': 8,
                    'digest_type': 1,
                    'digest': '012356789ABCDEF0123456789ABCDEF012345678',
                    'flags': 257,
                    'protocol': 3,
                    'public_key':
                        'MuhdzsQdqEGShwjtJDKZZjdKqUSGluFzTTinpuEeIRzLLcgkwgAPKWFa '
                        'eQntNlmcNDeCziGwpdvhJnvKXEMbFcZwsaDIJuWqERxAQNGABWfPlCLh '
                        'HQPnbpRPNKipSdBaUhuOubvFvjBpFAwiwSAapRDVsAgKvjXucfXpFfYb '
                        'pCundbAXBWhbpHVbqgmGoixXzFSwUsGVYLPpBCiDlLJwzjRKYYaoVYge '
                        'kMtKFYUVnWIKbectWkDFdVqXwkKigCUDiuTTJxOBRJRNzGiDNMWBjYSm '
                        'bBCAHMaMYaghLbYTwyKXltdHTHwBwtswGNfpnEdSpKFzZJonBZArQfHD '
                        'lfceKgmKwEF=',
                },
                {
                    'key_tag': 12345,
                    'algorithm': 8,
                    'digest_type': 2,
                    'digest': '0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF0123456789ABCDEF',
                    'flags': 257,
                    'protocol': 3,
                    'public_key':
                        'MuhdzsQdqEGShwjtJDKZZjdKqUSGluFzTTinpuEeIRzLLcgkwgAPKWFa '
                        'eQntNlmcNDeCziGwpdvhJnvKXEMbFcZwsaDIJuWqERxAQNGABWfPlCLh '
                        'HQPnbpRPNKipSdBaUhuOubvFvjBpFAwiwSAapRDVsAgKvjXucfXpFfYb '
                        'pCundbAXBWhbpHVbqgmGoixXzFSwUsGVYLPpBCiDlLJwzjRKYYaoVYge '
                        'kMtKFYUVnWIKbectWkDFdVqXwkKigCUDiuTTJxOBRJRNzGiDNMWBjYSm '
                        'bBCAHMaMYaghLbYTwyKXltdHTHwBwtswGNfpnEdSpKFzZJonBZArQfHD '
                        'lfceKgmKwEF=',
                }
            ],
        }
