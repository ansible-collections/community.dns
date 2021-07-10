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

from ansible_collections.community.dns.plugins.modules import hosttech_dns_records

# These imports are needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.wsdl
import ansible_collections.community.dns.plugins.module_utils.json_api_helper

from .helper import (
    expect_wsdl_authentication,
    expect_wsdl_value,
    validate_wsdl_call,
    validate_wsdl_add_request,
    validate_wsdl_update_request,
    validate_wsdl_del_request,
    create_wsdl_add_result,
    create_wsdl_update_result,
    create_wsdl_del_result,
    WSDL_DEFAULT_ZONE_RESULT,
    WSDL_ZONE_NOT_FOUND,
    JSON_ZONE_GET_RESULT,
    JSON_ZONE_LIST_RESULT,
)

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False


@pytest.mark.skipif(not HAS_LXML_ETREE, reason="Need lxml.etree for WSDL tests")
class TestHosttechDNSRecordWSDL(ModuleTestCase):
    def test_unknown_zone(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.org',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_ZONE_NOT_FOUND),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleFailJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.org',
                    'records': [],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['msg'] == 'Zone not found'

    def test_unknown_zone_id(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    '23',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_ZONE_NOT_FOUND),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleFailJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone_id': 23,
                    'records': [],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['msg'] == 'Zone not found'

    def test_idempotency_present(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_DEFAULT_ZONE_RESULT),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.com',
                    'records': [
                        {
                            'prefix': '',
                            'type': 'A',
                            'value': '1.2.3.4',
                        },
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False
        assert e.value.args[0]['zone_id'] == 42

    def test_change_add_one_check_mode(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_DEFAULT_ZONE_RESULT),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.com',
                    'records': [
                        {
                            'record': 'example.com',
                            'type': 'CAA',
                            'ttl': 3600,
                            'value': [
                                'test',
                            ],
                        }
                    ],
                    '_ansible_check_mode': True,
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True
        assert e.value.args[0]['zone_id'] == 42

    def test_change_add_one(self):
        new_entry = (131, 42, 'CAA', 'foo', 'test', 3600, None, None)
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_DEFAULT_ZONE_RESULT),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_add_request('42', new_entry),
            ]))
            .result_str(create_wsdl_add_result(new_entry)),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.com',
                    'records': [
                        {
                            'record': 'foo.example.com',
                            'type': 'CAA',
                            'ttl': 3600,
                            'value': [
                                'test',
                            ],
                        }
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True
        assert e.value.args[0]['zone_id'] == 42

    def test_change_modify_list(self):
        del_entry = (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None)
        update_entry = (131, 42, 'NS', '', 'ns4.hostserv.eu', 10800, None, None)
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                expect_wsdl_value(
                    [lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(WSDL_DEFAULT_ZONE_RESULT),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_del_request(del_entry),
            ]))
            .result_str(create_wsdl_del_result(True)),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_wsdl_authentication('foo', 'bar'),
                validate_wsdl_update_request(update_entry),
            ]))
            .result_str(create_wsdl_update_result(update_entry)),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.com',
                    'records': [
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
                })
                hosttech_dns_records.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True
        assert e.value.args[0]['zone_id'] == 42
        assert 'diff' in e.value.args[0]
        assert 'before' in e.value.args[0]['diff']
        assert 'after' in e.value.args[0]['diff']
        assert e.value.args[0]['diff']['before'] == {
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
                },
            ],
        }
        assert e.value.args[0]['diff']['after'] == {
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
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }


class TestHosttechDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_records.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.json_api_helper.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone': 'example.org',
            'records': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
        ])

        assert result['msg'] == 'Zone not found'

    def test_unknown_zone_id(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'records': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone': 'example.org',
            'records': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 23,
            'records': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone': 'example.org',
            'records': [],
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
        result = self.run_module_failed(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
        ])

        assert result['msg'] == 'Found multiple entries for record test.example.com and type A: index #0 and #1'

    def test_idempotency_empty(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 42,
            'records': [],
            '_ansible_remote_tmp': '/tmp/tmp',
            '_ansible_keep_remote_files': True,
        }, [
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is False
        assert result['zone_id'] == 42

    def test_removal_prune(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
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
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'ttl': 10800,
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
                },
            ],
        }

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one_check_mode_prefix(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone_id': 42,
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
        ])

        assert result['changed'] is True
        assert result['zone_id'] == 42

    def test_change_add_one(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.com')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone': 'example.com',
            'records': [
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
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }

    def test_change_modify_list_ttl(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_records, {
            'hosttech_token': 'foo',
            'zone': 'example.com',
            'records': [
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
            .result_json(JSON_ZONE_LIST_RESULT),
            FetchUrlCall('GET', 200)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_GET_RESULT),
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
                    'ttl': 10800,
                    'type': 'NS',
                    'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
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
                    'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
                },
            ],
        }
