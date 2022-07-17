# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import sys
import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import MagicMock

lxmletree = pytest.importorskip("lxml.etree")

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    Parser,
    Composer,
)


def test_composer_generation():
    composer = Composer(MagicMock(), api='https://example.com/api')
    composer.add_simple_command(
        'test',
        int_value=42,
        str_value='bar',
        list_value=[1, 2, 3],
        dict_value={
            'hello': 'world',
            'list': [2, 3, 5, 7],
        }
    )
    command = to_native(lxmletree.tostring(composer._root, pretty_print=True)).splitlines()

    print(command)

    expected_lines = [
        '  <SOAP-ENV:Header/>',
        '  <SOAP-ENV:Body>',
        '    <ns0:test xmlns:ns0="https://example.com/api">',
        '      <int_value xsi:type="xsd:int">42</int_value>',
        '      <str_value xsi:type="xsd:string">bar</str_value>',
        '      <list_value xsi:type="SOAP-ENC:Array">',
        '        <item xsi:type="xsd:int">1</item>',
        '        <item xsi:type="xsd:int">2</item>',
        '        <item xsi:type="xsd:int">3</item>',
        '      </list_value>',
        '      <dict_value xmlns:ns0="http://xml.apache.org/xml-soap" xsi:type="ns0:Map">',
        '        <item>',
        '          <key xsi:type="xsd:string">hello</key>',
        '          <value xsi:type="xsd:string">world</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">list</key>',
        '          <value xsi:type="SOAP-ENC:Array">',
        '            <item xsi:type="xsd:int">2</item>',
        '            <item xsi:type="xsd:int">3</item>',
        '            <item xsi:type="xsd:int">5</item>',
        '            <item xsi:type="xsd:int">7</item>',
        '          </value>',
        '        </item>',
        '      </dict_value>',
        '    </ns0:test>',
        '  </SOAP-ENV:Body>',
        '</SOAP-ENV:Envelope>',
    ]

    if sys.version_info < (3, 7):
        assert sorted(command[1:]) == sorted(expected_lines)
    else:
        assert command[1:] == expected_lines

    for part in [
            '<SOAP-ENV:Envelope',
            ' xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"',
            ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            ' xmlns:ns2="auth"',
            ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"',
            ' SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"',
    ]:
        assert part in command[0]


def test_parsing():
    input = '\n'.join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        ''.join([
            '<SOAP-ENV:Envelope',
            ' xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"',
            ' xmlns:ns1="https://example.com/api"',
            ' xmlns:xsd="http://www.w3.org/2001/XMLSchema"',
            ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
            ' xmlns:ns2="http://xml.apache.org/xml-soap"',
            ' xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"',
            ' SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"',
            '>',
        ]),
        '  <SOAP-ENV:Header>',
        '    <ns1:authenticateResponse>',
        '      <return xsi:type="xsd:boolean">true</return>',
        '    </ns1:authenticateResponse>',
        '  </SOAP-ENV:Header>',
        '  <SOAP-ENV:Body>',
        '    <ns1:getZoneResponse>',
        '      <return xsi:type="ns2:Map">',
        '        <item>',
        '          <key xsi:type="xsd:string">id</key>',
        '          <value xsi:type="xsd:int">1</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">user</key>',
        '          <value xsi:type="xsd:int">2</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">name</key>',
        '          <value xsi:type="xsd:string">example.com</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">email</key>',
        '          <value xsi:type="xsd:string">info@example.com</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">ttl</key>',
        '          <value xsi:type="xsd:int">10800</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">nameserver</key>',
        '          <value xsi:type="xsd:string">ns1.hostserv.eu</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">serial</key>',
        '          <value xsi:type="xsd:string">1234567890</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">serialLastUpdate</key>',
        '          <value xsi:type="xsd:int">0</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">refresh</key>',
        '          <value xsi:type="xsd:int">7200</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">retry</key>',
        '          <value xsi:type="xsd:int">120</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">expire</key>',
        '          <value xsi:type="xsd:int">1234567</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">template</key>',
        '          <value xsi:nil="true"/>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">ns3</key>',
        '          <value xsi:type="xsd:int">1</value>',
        '        </item>',
        '        <item>',
        '          <key xsi:type="xsd:string">records</key>',
        '          <value SOAP-ENC:arrayType="ns2:Map[2]" xsi:type="SOAP-ENC:Array">',
        '            <item xsi:type="ns2:Map">',
        '              <item>',
        '                <key xsi:type="xsd:string">id</key>',
        '                <value xsi:type="xsd:int">3</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">zone</key>',
        '                <value xsi:type="xsd:int">4</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">type</key>',
        '                <value xsi:type="xsd:string">A</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">prefix</key>',
        '                <value xsi:type="xsd:string"></value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">target</key>',
        '                <value xsi:type="xsd:string">1.2.3.4</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">ttl</key>',
        '                <value xsi:type="xsd:int">3600</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">comment</key>',
        '                <value xsi:nil="true"/>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">priority</key>',
        '                <value xsi:nil="true"/>',
        '              </item>',
        '            </item>',
        '            <item xsi:type="ns2:Map">',
        '              <item>',
        '                <key xsi:type="xsd:string">id</key>',
        '                <value xsi:type="xsd:int">5</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">zone</key>',
        '                <value xsi:type="xsd:int">4</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">type</key>',
        '                <value xsi:type="xsd:string">A</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">prefix</key>',
        '                <value xsi:type="xsd:string">*</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">target</key>',
        '                <value xsi:type="xsd:string">1.2.3.5</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">ttl</key>',
        '                <value xsi:type="xsd:int">3600</value>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">comment</key>',
        '                <value xsi:nil="true"/>',
        '              </item>',
        '              <item>',
        '                <key xsi:type="xsd:string">priority</key>',
        '                <value xsi:nil="true"/>',
        '              </item>',
        '            </item>',
        '          </value>',
        '        </item>',
        '      </return>',
        '    </ns1:getZoneResponse>',
        '  </SOAP-ENV:Body>',
        '</SOAP-ENV:Envelope>',
    ]).encode('utf-8')

    parser = Parser('https://example.com/api', lxmletree.fromstring(input))
    assert parser.get_header('authenticateResponse') is True
    assert len(parser._header) == 1
    assert parser.get_result('getZoneResponse') == {
        'id': 1,
        'user': 2,
        'name': 'example.com',
        'email': 'info@example.com',
        'ttl': 10800,
        'nameserver': 'ns1.hostserv.eu',
        'serial': '1234567890',
        'serialLastUpdate': 0,
        'refresh': 7200,
        'retry': 120,
        'expire': 1234567,
        'template': None,
        'ns3': 1,
        'records': [
            {
                'id': 3,
                'zone': 4,
                'type': 'A',
                'prefix': None,
                'target': '1.2.3.4',
                'ttl': 3600,
                'comment': None,
                'priority': None,
            },
            {
                'id': 5,
                'zone': 4,
                'type': 'A',
                'prefix': '*',
                'target': '1.2.3.5',
                'ttl': 3600,
                'comment': None,
                'priority': None,
            },
        ],
    }
    assert len(parser._body) == 1
