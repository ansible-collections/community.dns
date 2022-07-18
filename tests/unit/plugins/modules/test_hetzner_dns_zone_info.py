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

from ansible_collections.community.dns.plugins.modules import hetzner_dns_zone_info

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.http  # noqa

from .hetzner import (
    HETZNER_JSON_ZONE_GET_RESULT,
    HETZNER_JSON_ZONE_LIST_RESULT,
)


class TestHetznerDNSZoneInfoJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hetzner_dns_zone_info.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.http.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.org')
            .return_header('Content-Type', 'application/json; charset=utf-8')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_id': '23',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 404)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/23')
            .return_header('Content-Type', 'application/json; charset=utf-8')
            .result_json(dict(message="")),
        ])

        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
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
        result = self.run_module_failed(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_id': '23',
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
        result = self.run_module_failed(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.org',
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

    def test_get(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_name': 'example.com',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones', without_query=True)
            .expect_query_values('name', 'example.com')
            .return_header('Content-Type', 'application/json; charset=utf-8')
            .result_json(HETZNER_JSON_ZONE_LIST_RESULT),
        ])
        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert result['zone_name'] == 'example.com'
        assert result['zone_info'] == {
            'created': '2021-07-09T11:18:37Z',
            'modified': '2021-07-09T11:18:37Z',
            'legacy_dns_host': 'string',
            'legacy_ns': ['bar', 'foo'],
            'ns': ['string'],
            'owner': 'Example',
            'paused': True,
            'permission': 'string',
            'project': 'string',
            'registrar': 'string',
            'status': 'verified',
            'ttl': 10800,
            'verified': '2021-07-09T11:18:37Z',
            'records_count': 0,
            'is_secondary_dns': True,
            'txt_verification': {
                'name': 'string',
                'token': 'string',
            },
        }

    def test_get_id(self, mocker):
        result = self.run_module_success(mocker, hetzner_dns_zone_info, {
            'hetzner_token': 'foo',
            'zone_id': '42',
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('auth-api-token', 'foo')
            .expect_url('https://dns.hetzner.com/api/v1/zones/42')
            .return_header('Content-Type', 'application/json; charset=utf-8')
            .result_json(HETZNER_JSON_ZONE_GET_RESULT),
        ])
        assert result['changed'] is False
        assert result['zone_id'] == '42'
        assert result['zone_name'] == 'example.com'
        assert result['zone_info'] == {
            'created': '2021-07-09T11:18:37Z',
            'modified': '2021-07-09T11:18:37Z',
            'legacy_dns_host': 'string',
            'legacy_ns': ['bar', 'foo'],
            'ns': ['string'],
            'owner': 'Example',
            'paused': True,
            'permission': 'string',
            'project': 'string',
            'registrar': 'string',
            'status': 'verified',
            'ttl': 10800,
            'verified': '2021-07-09T11:18:37Z',
            'records_count': 0,
            'is_secondary_dns': True,
            'txt_verification': {
                'name': 'string',
                'token': 'string',
            },
        }
