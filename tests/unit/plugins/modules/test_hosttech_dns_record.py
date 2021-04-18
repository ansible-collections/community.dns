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
    AnsibleFailJson,
)

from ansible_collections.community.dns.plugins.modules import hosttech_dns_record

# This import is needed so patching below works
import ansible_collections.community.dns.plugins.module_utils.wsdl

from .helper import (
    add_answer_end_lines,
    add_answer_start_lines,
    add_dns_record_lines,
    check_nil,
    check_value,
    expect_authentication,
    expect_value,
    find_map_entry,
    get_value,
    validate_wsdl_call,
    DEFAULT_ENTRIES,
    DEFAULT_ZONE_RESULT,
)

lxmletree = pytest.importorskip("lxml.etree")


def check_record(record_data, entry):
    check_value(find_map_entry(record_data, 'type'), entry[2], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    prefix = find_map_entry(record_data, 'prefix')
    if entry[3]:
        check_value(prefix, entry[3], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    elif prefix is not None:
        check_nil(prefix)
    check_value(find_map_entry(record_data, 'target'), entry[4], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    check_value(find_map_entry(record_data, 'ttl'), str(entry[5]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
    if entry[6] is None:
        comment = find_map_entry(record_data, 'comment', allow_non_existing=True)
        if comment is not None:
            check_nil(comment)
    else:
        check_value(find_map_entry(record_data, 'comment'), entry[6], type=('http://www.w3.org/2001/XMLSchema', 'string'))
    if entry[7] is None:
        check_nil(find_map_entry(record_data, 'priority'))
    else:
        check_value(find_map_entry(record_data, 'priority'), entry[7], type=('http://www.w3.org/2001/XMLSchema', 'string'))


def validate_add_request(zone, entry):
    def predicate(content, header, body):
        fn_data = get_value(body, lxmletree.QName('https://ns1.hosttech.eu/public/api', 'addRecord').text)
        check_value(get_value(fn_data, 'search'), zone, type=('http://www.w3.org/2001/XMLSchema', 'string'))
        check_record(get_value(fn_data, 'recorddata'), entry)
        return True

    return predicate


def validate_update_request(entry):
    def predicate(content, header, body):
        fn_data = get_value(body, lxmletree.QName('https://ns1.hosttech.eu/public/api', 'updateRecord').text)
        check_value(get_value(fn_data, 'recordId'), str(entry[0]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
        check_record(get_value(fn_data, 'recorddata'), entry)
        return True

    return predicate


def validate_del_request(entry):
    def predicate(content, header, body):
        fn_data = get_value(body, lxmletree.QName('https://ns1.hosttech.eu/public/api', 'deleteRecord').text)
        check_value(get_value(fn_data, 'recordId'), str(entry[0]), type=('http://www.w3.org/2001/XMLSchema', 'int'))
        return True

    return predicate


def create_add_result(entry):
    lines = []
    add_answer_start_lines(lines)
    lines.append('<ns1:addRecordResponse>')
    add_dns_record_lines(lines, entry, 'return')
    lines.append('</ns1:addRecordResponse>')
    add_answer_end_lines(lines)
    return ''.join(lines)


def create_update_result(entry):
    lines = []
    add_answer_start_lines(lines)
    lines.append('<ns1:updateRecordResponse>')
    add_dns_record_lines(lines, entry, 'return')
    lines.append('</ns1:updateRecordResponse>')
    add_answer_end_lines(lines)
    return ''.join(lines)


def create_del_result(success):
    lines = []
    add_answer_start_lines(lines)
    lines.extend([
        '<ns1:deleteRecordResponse>',
        '<return xsi:type="xsd:boolean">{success}</return>'.format(success='true' if success else 'false'),
        '</ns1:deleteRecordResponse>',
    ])
    add_answer_end_lines(lines)
    return ''.join(lines)


class TestHosttechDNSRecord(ModuleTestCase):
    def test_idempotency_present(self):
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
        record = DEFAULT_ENTRIES[0]
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
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                validate_del_request(record),
            ]))
            .result_str(create_del_result(True)),
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
                expect_authentication('foo', 'bar'),
                expect_value(
                    [lxmletree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(DEFAULT_ZONE_RESULT),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                validate_add_request('42', new_entry),
            ]))
            .result_str(create_add_result(new_entry)),
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
                expect_authentication('foo', 'bar'),
                expect_value(
                    [lxmletree.QName('https://ns1.hosttech.eu/public/api', 'getZone').text, 'sZoneName'],
                    'example.com',
                    ('http://www.w3.org/2001/XMLSchema', 'string')
                ),
            ]))
            .result_str(DEFAULT_ZONE_RESULT),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                validate_del_request(del_entry),
            ]))
            .result_str(create_del_result(True)),
            OpenUrlCall('POST', 200)
            .expect_content_predicate(validate_wsdl_call([
                expect_authentication('foo', 'bar'),
                validate_update_request(update_entry),
            ]))
            .result_str(create_update_result(update_entry)),
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
