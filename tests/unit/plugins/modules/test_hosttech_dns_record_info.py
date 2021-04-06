# (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch

from ansible_collections.community.internal_test_tools.tests.unit.utils.open_url_framework import (
    OpenUrlCall,
    OpenUrlProxy,
)

from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    set_module_args,
    ModuleTestCase,
    AnsibleExitJson,
    # AnsibleFailJson,
)

from ansible_collections.community.dns.plugins.modules import hosttech_dns_record_info

# This import is needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.wsdl

from .helper import (
    expect_authentication,
    expect_value,
    validate_wsdl_call,
    DEFAULT_ZONE_RESULT,
)

lxmletree = pytest.importorskip("lxml.etree")


class TestHosttechDNSRecordInfo(ModuleTestCase):
    def test_get_single(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                expect_value(
                    [lxmletree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(DEFAULT_ZONE_RESULT),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'A',
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record_info.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False
        assert 'set' in e.value.args[0]
        assert e.value.args[0]['set']['record'] == 'example.com'
        assert e.value.args[0]['set']['ttl'] == 3600
        assert e.value.args[0]['set']['type'] == 'A'
        assert e.value.args[0]['set']['value'] == ['1.2.3.4']
        assert 'sets' not in e.value.args[0]

    def test_get_all_for_one_record(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                expect_value(
                    [lxmletree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(DEFAULT_ZONE_RESULT),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'what': 'all_types_for_record',
                    'zone': 'example.com',
                    'record': '*.example.com',
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record_info.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False
        assert 'set' not in e.value.args[0]
        assert 'sets' in e.value.args[0]
        sets = e.value.args[0]['sets']
        assert len(sets) == 2
        assert sets[0] == {
            'record': '*.example.com',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.5'],
        }
        assert sets[1] == {
            'record': '*.example.com',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::4'],
        }

    def test_get_all(self):
        open_url = OpenUrlProxy([
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                expect_value(
                    [lxmletree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(DEFAULT_ZONE_RESULT),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'what': 'all_records',
                    'zone': 'example.com.',
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record_info.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False
        assert 'set' not in e.value.args[0]
        assert 'sets' in e.value.args[0]
        sets = e.value.args[0]['sets']
        assert len(sets) == 6
        assert sets[0] == {
            'record': '*.example.com',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.5'],
        }
        assert sets[1] == {
            'record': '*.example.com',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::4'],
        }
        assert sets[2] == {
            'record': 'example.com',
            'ttl': 3600,
            'type': 'A',
            'value': ['1.2.3.4'],
        }
        assert sets[3] == {
            'record': 'example.com',
            'ttl': 3600,
            'type': 'AAAA',
            'value': ['2001:1:2::3'],
        }
        assert sets[4] == {
            'record': 'example.com',
            'ttl': 3600,
            'type': 'MX',
            'value': ['example.com'],
        }
        assert sets[5] == {
            'record': 'example.com',
            'ttl': 10800,
            'type': 'NS',
            'value': ['ns3.hostserv.eu', 'ns2.hostserv.eu', 'ns1.hostserv.eu'],
        }
