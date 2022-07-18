# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

try:
    import lxml.etree
except ImportError:
    # should be handled in module importing this one
    pass


HOSTTECH_WSDL_DEFAULT_ENTRIES = [
    (125, 42, 'A', '', '1.2.3.4', 3600, None, None),
    (126, 42, 'A', '*', '1.2.3.5', 3600, None, None),
    (127, 42, 'AAAA', '', '2001:1:2::3', 3600, None, None),
    (128, 42, 'AAAA', '*', '2001:1:2::4', 3600, None, None),
    (129, 42, 'MX', '', 'example.com', 3600, None, '10'),
    (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None),
    (131, 42, 'NS', '', 'ns2.hostserv.eu', 10800, None, None),
    (132, 42, 'NS', '', 'ns1.hostserv.eu', 10800, None, None),
]

HOSTTECH_JSON_DEFAULT_ENTRIES = [
    # (125, 42, 'A', '', '1.2.3.4', 3600, None, None),
    {
        'id': 125,
        'type': 'A',
        'name': '',
        'ipv4': '1.2.3.4',
        'ttl': 3600,
        'comment': '',
    },
    # (126, 42, 'A', '*', '1.2.3.5', 3600, None, None),
    {
        'id': 126,
        'type': 'A',
        'name': '*',
        'ipv4': '1.2.3.5',
        'ttl': 3600,
        'comment': '',
    },
    # (127, 42, 'AAAA', '', '2001:1:2::3', 3600, None, None),
    {
        'id': 127,
        'type': 'AAAA',
        'name': '',
        'ipv6': '2001:1:2::3',
        'ttl': 3600,
        'comment': '',
    },
    # (128, 42, 'AAAA', '*', '2001:1:2::4', 3600, None, None),
    {
        'id': 128,
        'type': 'AAAA',
        'name': '*',
        'ipv6': '2001:1:2::4',
        'ttl': 3600,
        'comment': '',
    },
    # (129, 42, 'MX', '', 'example.com', 3600, None, '10'),
    {
        'id': 129,
        'type': 'MX',
        'ownername': '',
        'name': 'example.com',
        'pref': 10,
        'ttl': 3600,
        'comment': '',
    },
    # (130, 42, 'NS', '', 'ns3.hostserv.eu', 10800, None, None),
    {
        'id': 130,
        'type': 'NS',
        'ownername': '',
        'targetname': 'ns3.hostserv.eu',
        'ttl': 10800,
        'comment': '',
    },
    # (131, 42, 'NS', '', 'ns2.hostserv.eu', 10800, None, None),
    {
        'id': 131,
        'type': 'NS',
        'ownername': '',
        'targetname': 'ns2.hostserv.eu',
        'ttl': 10800,
        'comment': '',
    },
    # (132, 42, 'NS', '', 'ns1.hostserv.eu', 10800, None, None),
    {
        'id': 132,
        'type': 'NS',
        'ownername': '',
        'targetname': 'ns1.hostserv.eu',
        'ttl': 10800,
        'comment': '',
    },
]


def validate_wsdl_call(conditions):
    def predicate(content):
        assert content.startswith(b"<?xml version='1.0' encoding='utf-8'?>\n")

        root = lxml.etree.fromstring(content)
        header = None
        body = None

        for header_ in root.iter(lxml.etree.QName('http://schemas.xmlsoap.org/soap/envelope/', 'Header').text):
            header = header_
        for body_ in root.iter(lxml.etree.QName('http://schemas.xmlsoap.org/soap/envelope/', 'Body').text):
            body = body_

        for condition in conditions:
            if not condition(content, header, body):
                return False
        return True

    return predicate


def get_wsdl_value(root, name):
    for auth in root.iter(name):
        return auth
    raise Exception('Cannot find child "{0}" in node {1}: {2}'.format(name, root, lxml.etree.tostring(root)))


def expect_wsdl_authentication(username, password):
    def predicate(content, header, body):
        auth = get_wsdl_value(header, lxml.etree.QName('auth', 'authenticate').text)
        assert get_wsdl_value(auth, 'UserName').text == username
        assert get_wsdl_value(auth, 'Password').text == password
        return True

    return predicate


def check_wsdl_nil(node):
    nil_flag = node.get(lxml.etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'nil'))
    if nil_flag != 'true':
        print(nil_flag)
    assert nil_flag == 'true'


def check_wsdl_value(node, value, type=None):
    if type is not None:
        type_text = node.get(lxml.etree.QName('http://www.w3.org/2001/XMLSchema-instance', 'type'))
        assert type_text is not None, 'Cannot find type in {0}: {1}'.format(node, lxml.etree.tostring(node))
        i = type_text.find(':')
        if i < 0:
            ns = None
        else:
            ns = node.nsmap.get(type_text[:i])
            type_text = type_text[i + 1:]
        if ns != type[0] or type_text != type[1]:
            print(ns, type[0], type_text, type[1])
        assert ns == type[0] and type_text == type[1]
    if node.text != value:
        print(node.text, value)
    assert node.text == value


def find_xml_map_entry(map_root, key_name, allow_non_existing=False):
    for map_entry in map_root.iter('item'):
        key = get_wsdl_value(map_entry, 'key')
        value = get_wsdl_value(map_entry, 'value')
        if key.text == key_name:
            check_wsdl_value(key, key_name, type=('http://www.w3.org/2001/XMLSchema', 'string'))
            return value
    if allow_non_existing:
        return None
    raise Exception('Cannot find map entry with key "{0}" in node {1}: {2}'.format(key_name, map_root, lxml.etree.tostring(map_root)))


def expect_wsdl_value(path, value, type=None):
    def predicate(content, header, body):
        node = body
        for entry in path:
            node = get_wsdl_value(node, entry)
        check_wsdl_value(node, value, type=type)
        return True

    return predicate


def add_wsdl_answer_start_lines(lines):
    lines.extend([
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
        ' xmlns:ns1="https://ns1.hosttech.eu/public/api"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:ns2="http://xml.apache.org/xml-soap"'
        ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"'
        ' SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">',
        '<SOAP-ENV:Header>',
        '<ns1:authenticateResponse>',
        '<return xsi:type="xsd:boolean">true</return>',
        '</ns1:authenticateResponse>',
        '</SOAP-ENV:Header>',
        '<SOAP-ENV:Body>',
    ])


def add_wsdl_answer_end_lines(lines):
    lines.extend([
        '</SOAP-ENV:Body>',
        '</SOAP-ENV:Envelope>'
    ])


def add_wsdl_dns_record_lines(lines, entry, tag_name):
    lines.extend([
        '<{tag_name} xsi:type="ns2:Map">'.format(tag_name=tag_name),
        '<item><key xsi:type="xsd:string">id</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[0]),
        '<item><key xsi:type="xsd:string">zone</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[1]),
        '<item><key xsi:type="xsd:string">type</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[2]),
        '<item><key xsi:type="xsd:string">prefix</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[3]),
        '<item><key xsi:type="xsd:string">target</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[4]),
        '<item><key xsi:type="xsd:string">ttl</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[5]),
    ])
    if entry[6] is None:
        lines.append('<item><key xsi:type="xsd:string">comment</key><value xsi:nil="true"/></item>')
    else:
        lines.append('<item><key xsi:type="xsd:string">comment</key><value xsi:type="xsd:string">{value}</value></item>'.format(value=entry[6]))
    if entry[7] is None:
        lines.append('<item><key xsi:type="xsd:string">priority</key><value xsi:nil="true"/></item>')
    else:
        lines.append('<item><key xsi:type="xsd:string">priority</key><value xsi:type="xsd:int">{value}</value></item>'.format(value=entry[7]))
    lines.append('</{tag_name}>'.format(tag_name=tag_name))


def create_wsdl_zones_answer(zone_id, zone_name, entries):
    lines = []
    add_wsdl_answer_start_lines(lines)
    lines.extend([
        '<ns1:getZoneResponse>',
        '<return xsi:type="ns2:Map">',
        '<item><key xsi:type="xsd:string">id</key><value xsi:type="xsd:int">{zone_id}</value></item>'.format(zone_id=zone_id),
        '<item><key xsi:type="xsd:string">user</key><value xsi:type="xsd:int">23</value></item>',
        '<item><key xsi:type="xsd:string">name</key><value xsi:type="xsd:string">{zone_name}</value></item>'.format(zone_name=zone_name),
        '<item><key xsi:type="xsd:string">email</key><value xsi:type="xsd:string">dns@hosttech.eu</value></item>',
        '<item><key xsi:type="xsd:string">ttl</key><value xsi:type="xsd:int">10800</value></item>',
        '<item><key xsi:type="xsd:string">nameserver</key><value xsi:type="xsd:string">ns1.hostserv.eu</value></item>',
        '<item><key xsi:type="xsd:string">serial</key><value xsi:type="xsd:string">12345</value></item>',
        '<item><key xsi:type="xsd:string">serialLastUpdate</key><value xsi:type="xsd:int">0</value></item>',
        '<item><key xsi:type="xsd:string">refresh</key><value xsi:type="xsd:int">7200</value></item>',
        '<item><key xsi:type="xsd:string">retry</key><value xsi:type="xsd:int">120</value></item>',
        '<item><key xsi:type="xsd:string">expire</key><value xsi:type="xsd:int">1234567</value></item>',
        '<item><key xsi:type="xsd:string">template</key><value xsi:nil="true"/></item>',
        '<item><key xsi:type="xsd:string">ns3</key><value xsi:type="xsd:int">1</value></item>',
    ])
    lines.append(
        '<item><key xsi:type="xsd:string">records</key><value SOAP-ENC:arrayType="ns2:Map[{count}]" xsi:type="SOAP-ENC:Array">'.format(
            count=len(entries)))
    for entry in entries:
        add_wsdl_dns_record_lines(lines, entry, 'item')
    lines.extend([
        '</value>',
        '</item>',
        '</return>',
        '</ns1:getZoneResponse>',
    ])
    add_wsdl_answer_end_lines(lines)
    return ''.join(lines)


def create_wsdl_zone_not_found_answer():
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"'
        ' xmlns:ns1="https://ns1.hosttech.eu/public/api"'
        ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"'
        ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' xmlns:ns2="http://xml.apache.org/xml-soap"'
        ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"'
        ' SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">',
        '<SOAP-ENV:Header>',
        '<ns1:authenticateResponse>',
        '<return xsi:type="xsd:boolean">true</return>',
        '</ns1:authenticateResponse>',
        '</SOAP-ENV:Header>',
        '<SOAP-ENV:Fault>',
        '<faultstring>zone not found</faultstring>'
        '</SOAP-ENV:Fault>',
        '</SOAP-ENV:Envelope>'
    ]
    return ''.join(lines)


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


HOSTTECH_WSDL_DEFAULT_ZONE_RESULT = create_wsdl_zones_answer(42, 'example.com', HOSTTECH_WSDL_DEFAULT_ENTRIES)

HOSTTECH_WSDL_ZONE_NOT_FOUND = create_wsdl_zone_not_found_answer()

HOSTTECH_JSON_ZONE_LIST_RESULT = {
    "data": [
        {
            "id": 42,
            "name": "example.com",
            "email": "test@example.com",
            "ttl": 10800,
            "nameserver": "ns1.hosttech.ch",
            "dnssec": False,
        },
        {
            "id": 43,
            "name": "foo.com",
            "email": "test@foo.com",
            "ttl": 10800,
            "nameserver": "ns1.hosttech.ch",
            'dnssec': True,
            'dnssec_email': 'test@foo.com',
        },
    ],
}

HOSTTECH_JSON_ZONE_GET_RESULT = {
    "data": {
        "id": 42,
        "name": "example.com",
        "email": "test@example.com",
        "ttl": 10800,
        "nameserver": "ns1.hosttech.ch",
        "dnssec": False,
        "records": HOSTTECH_JSON_DEFAULT_ENTRIES,
    }
}

HOSTTECH_JSON_ZONE_2_GET_RESULT = {
    "data": {
        "id": 43,
        "name": "foo.com",
        "email": "test@foo.com",
        "ttl": 10800,
        "nameserver": "ns1.hosttech.ch",
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
        "records": [],
    }
}

HOSTTECH_JSON_ZONE_RECORDS_GET_RESULT = {
    "data": HOSTTECH_JSON_DEFAULT_ENTRIES,
}
