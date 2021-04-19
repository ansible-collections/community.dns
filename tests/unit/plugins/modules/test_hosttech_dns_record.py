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

from ansible_collections.community.dns.plugins.modules import hosttech_dns_record

# This import is needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.wsdl
import ansible_collections.community.dns.plugins.module_utils.hosttech.json_api

from .helper import (
    add_wsdl_answer_end_lines,
    add_wsdl_answer_start_lines,
    add_wsdl_dns_record_lines,
    check_wsdl_nil,
    check_wsdl_value,
    expect_wsdl_authentication,
    expect_wsdl_value,
    find_xml_map_entry,
    get_wsdl_value,
    validate_wsdl_call,
    WSDL_DEFAULT_ENTRIES,
    WSDL_DEFAULT_ZONE_RESULT,
    WSDL_ZONE_NOT_FOUND,
    JSON_DEFAULT_ENTRIES,
    JSON_ZONE_GET_RESULT,
    JSON_ZONE_LIST_RESULT,
)

try:
    import lxml.etree
    HAS_LXML_ETREE = True
except ImportError:
    HAS_LXML_ETREE = False


def check_wsdl_record(record_data, entry):
    check_wsdl_value(find_xml_map_entry(record_data, 'type'), entry[2], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    prefix = find_xml_map_entry(record_data, 'prefix')
    if entry[3]:
        check_wsdl_value(prefix, entry[3], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    elif prefix is not None:
        check_wsdl_nil(prefix)
    check_wsdl_value(find_xml_map_entry(record_data, 'target'), entry[4], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    check_wsdl_value(find_xml_map_entry(record_data, 'ttl'), str(entry[5]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
    if entry[6] is None:
        comment = find_xml_map_entry(record_data, 'comment', allow_non_existing=True)
        if comment is not None:
            check_wsdl_nil(comment)
    else:
        check_wsdl_value(find_xml_map_entry(record_data, 'comment'), entry[6], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    if entry[7] is None:
        check_wsdl_nil(find_xml_map_entry(record_data, 'priority'))
    else:
        check_wsdl_value(find_xml_map_entry(record_data, 'priority'), entry[7], type=('http://www.w3.org/2001/XMLSchema', 'string'))


def validate_wsdl_add_request(zone, entry):
    def predicate(content, header, body):
        fn_data = get_wsdl_value(body, lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'addRecord').text)
        check_wsdl_value(get_wsdl_value(fn_data, 'search'), zone, type=('http://www.w3.org/2001/XMLSchema', 'string'))
        check_wsdl_record(get_wsdl_value(fn_data, 'recorddata'), entry)
        return True

    return predicate


def validate_wsdl_update_request(entry):
    def predicate(content, header, body):
        fn_data = get_wsdl_value(body, lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'updateRecord').text)
        check_wsdl_value(get_wsdl_value(fn_data, 'recordId'), str(entry[0]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
        check_wsdl_record(get_wsdl_value(fn_data, 'recorddata'), entry)
        return True

    return predicate


def validate_wsdl_del_request(entry):
    def predicate(content, header, body):
        fn_data = get_wsdl_value(body, lxml.etree.QName('https://ns1.hosttech.eu/public/api', 'deleteRecord').text)
        check_wsdl_value(get_wsdl_value(fn_data, 'recordId'), str(entry[0]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
        return True

    return predicate


def create_wsdl_add_result(entry):
    lines = []
    add_wsdl_answer_start_lines(lines)
    lines.append('<ns1:addRecordResponse>')
    add_wsdl_dns_record_lines(lines, entry, 'return')
    lines.append('</ns1:addRecordResponse>')
    add_wsdl_answer_end_lines(lines)
    return ''.join(lines)


def create_wsdl_update_result(entry):
    lines = []
    add_wsdl_answer_start_lines(lines)
    lines.append('<ns1:updateRecordResponse>')
    add_wsdl_dns_record_lines(lines, entry, 'return')
    lines.append('</ns1:updateRecordResponse>')
    add_wsdl_answer_end_lines(lines)
    return ''.join(lines)


def create_wsdl_del_result(success):
    lines = []
    add_wsdl_answer_start_lines(lines)
    lines.extend([
        '<ns1:deleteRecordResponse>',
        '<return xsi:type="xsd:boolean">{success}</return>'.format(success='true' if success else 'false'),
        '</ns1:deleteRecordResponse>',
    ])
    add_wsdl_answer_end_lines(lines)
    return ''.join(lines)


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
                    'state': 'present',
                    'zone': 'example.org',
                    'record': 'example.org',
                    'type': 'MX',
                    'ttl': 3600,
                    'value': [
                        '10 example.com',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

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
                    'state': 'present',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'MX',
                    'ttl': 3600,
                    'value': [
                        '10 example.com',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False

    def test_idempotency_absent_value(self):
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
                    'state': 'absent',
                    'zone': 'example.com',
                    'record': '*.example.com',
                    'type': 'A',
                    'ttl': 3600,
                    'value': [
                        '1.2.3.6',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False

    def test_idempotency_absent_ttl(self):
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
                    'state': 'absent',
                    'zone': 'example.com',
                    'record': '*.example.com',
                    'type': 'A',
                    'ttl': 1800,
                    'value': [
                        '1.2.3.5',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False

    def test_idempotency_absent_type(self):
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
                    'state': 'absent',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        'something',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False

    def test_idempotency_absent_record(self):
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
                    'state': 'absent',
                    'zone': 'example.com.',
                    'record': 'somewhere.example.com.',
                    'type': 'A',
                    'ttl': 3600,
                    'value': [
                        '1.2.3.6',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is False

    def test_absent(self):
        record = WSDL_DEFAULT_ENTRIES[0]
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
                validate_wsdl_del_request(record),
            ]))
            .result_str(create_wsdl_del_result(True)),
        ])
        with patch('ansible_collections.community.dns.plugins.module_utils.wsdl.open_url', open_url):
            with pytest.raises(AnsibleExitJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'state': 'absent',
                    'zone': 'example.com',
                    'record': record[3] + 'example.com',
                    'type': record[2],
                    'ttl': record[5],
                    'value': [
                        record[4],
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True

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
                    'state': 'present',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        'test',
                    ],
                    '_ansible_check_mode': True,
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True

    def test_change_add_one(self):
        new_entry = (131, 42, 'CAA', '', 'test', 3600, None, None)
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
                    'state': 'present',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'CAA',
                    'ttl': 3600,
                    'value': [
                        'test',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True

    def test_change_modify_list_fail(self):
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
            with pytest.raises(AnsibleFailJson) as e:
                set_module_args({
                    'hosttech_username': 'foo',
                    'hosttech_password': 'bar',
                    'state': 'present',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns4.hostserv.eu',
                    ],
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['failed'] is True
        assert e.value.args[0]['msg'] == "Record already exists with different value. Set 'overwrite' to replace it"

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
                    'state': 'present',
                    'zone': 'example.com',
                    'record': 'example.com',
                    'type': 'NS',
                    'ttl': 10800,
                    'value': [
                        'ns1.hostserv.eu',
                        'ns4.hostserv.eu',
                    ],
                    'overwrite': True,
                    '_ansible_diff': True,
                    '_ansible_remote_tmp': '/tmp/tmp',
                    '_ansible_keep_remote_files': True,
                })
                hosttech_dns_record.main()

        print(e.value.args[0])
        assert e.value.args[0]['changed'] is True
        assert 'diff' in e.value.args[0]
        assert 'before' in e.value.args[0]['diff']
        assert 'after' in e.value.args[0]['diff']
        assert e.value.args[0]['diff']['before'] == {
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert e.value.args[0]['diff']['after'] == {
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
        }


class TestHosttechDNSRecordJSON(BaseTestModule):
    MOCK_ANSIBLE_MODULEUTILS_BASIC_ANSIBLEMODULE = 'ansible_collections.community.dns.plugins.modules.hosttech_dns_record.AnsibleModule'
    MOCK_ANSIBLE_MODULEUTILS_URLS_FETCH_URL = 'ansible_collections.community.dns.plugins.module_utils.hosttech.json_api.fetch_url'

    def test_unknown_zone(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.org',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .return_header('Content-Type', 'application/json')
            .result_json(JSON_ZONE_LIST_RESULT),
        ])

        print(result)
        assert result['msg'] == 'Zone not found'

    def test_auth_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.org',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .result_str(''),
        ])

        print(result)
        assert result['msg'].startswith('Cannot authenticate: ')

    def test_other_error(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.org',
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
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones', without_query=True)
            .expect_query_values('query', 'example.org')
            .result_str(''),
        ])

        print(result)
        assert result['msg'].startswith('Error: GET https://api.ns1.hosttech.eu/api/user/v1/zones?')
        assert 'did not yield JSON data, but HTTP status code 500 with Content-Type' in result['msg']

    def test_idempotency_present(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.com',
            'record': 'example.com',
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

        print(result)
        assert result['changed'] is False

    def test_idempotency_absent_value(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
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

        print(result)
        assert result['changed'] is False

    def test_idempotency_absent_ttl(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone': 'example.com',
            'record': '*.example.com',
            'type': 'A',
            'ttl': 1800,
            'value': [
                '1.2.3.5',
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

        print(result)
        assert result['changed'] is False

    def test_idempotency_absent_type(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                'something',
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

        print(result)
        assert result['changed'] is False

    def test_idempotency_absent_record(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone': 'example.com.',
            'record': 'somewhere.example.com.',
            'type': 'A',
            'ttl': 3600,
            'value': [
                '1.2.3.6',
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

        print(result)
        assert result['changed'] is False

    def test_absent(self, mocker):
        record = JSON_DEFAULT_ENTRIES[0]
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'absent',
            'zone': 'example.com',
            'record': record['name'] + 'example.com',
            'type': record['type'],
            'ttl': record['ttl'],
            'value': [
                record['ipv4'],
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
            FetchUrlCall('DELETE', 204)
            .expect_header('accept', 'application/json')
            .expect_header('authorization', 'Bearer foo')
            .expect_url('https://api.ns1.hosttech.eu/api/user/v1/zones/42/records/{0}'.format(record['id']))
            .result_str(''),
        ])

        print(result)
        assert result['changed'] is True

    def test_change_add_one_check_mode(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                'test',
            ],
            '_ansible_check_mode': True,
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

        print(result)
        assert result['changed'] is True

    def test_change_add_one(self, mocker):
        new_entry = (131, 42, 'CAA', '', 'test', 3600, None, None)
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.com',
            'record': 'example.com',
            'type': 'CAA',
            'ttl': 3600,
            'value': [
                '128 issue letsencrypt.org xxx',
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

        print(result)
        assert result['changed'] is True

    def test_change_modify_list_fail(self, mocker):
        result = self.run_module_failed(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
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

        print(result)
        assert result['msg'] == "Record already exists with different value. Set 'overwrite' to replace it"

    def test_change_modify_list(self, mocker):
        result = self.run_module_success(mocker, hosttech_dns_record, {
            'hosttech_token': 'foo',
            'state': 'present',
            'zone': 'example.com',
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': [
                'ns1.hostserv.eu',
                'ns4.hostserv.eu',
            ],
            'overwrite': True,
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

        print(result)
        assert result['changed'] is True
        assert 'diff' in result
        assert 'before' in result['diff']
        assert 'after' in result['diff']
        assert result['diff']['before'] == {
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns2.hostserv.eu', 'ns3.hostserv.eu'],
        }
        assert result['diff']['after'] == {
            'record': 'example.com',
            'type': 'NS',
            'ttl': 10800,
            'value': ['ns1.hostserv.eu', 'ns4.hostserv.eu'],
        }
