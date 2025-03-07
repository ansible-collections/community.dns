# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.modules import nameserver_info
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.plugins.modules.utils import (
    AnsibleExitJson,
    AnsibleFailJson,
    ModuleTestCase,
    set_module_args,
)

from ..module_utils.resolver_helper import (
    create_mock_answer,
    create_mock_response,
    mock_query_udp,
    mock_resolver,
)


# We need dnspython
dns = pytest.importorskip('dns')


class TestNameserverInfo(ModuleTestCase):
    def test_single(self):
        fake_query = MagicMock()
        fake_query.question = 'Doctor Who?'
        resolver = mock_resolver(['1.1.1.1'], {})
        udp_sequence = [
            {
                'query_target': dns.name.from_unicode(u'com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'www.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'www.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                ), dns.rrset.from_rdata(
                    'www.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'example.org')
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with pytest.raises(AnsibleExitJson) as exc:
                        with set_module_args({
                            'name': ['www.example.com'],
                        }):
                            nameserver_info.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert len(exc.value.args[0]['results']) == 1
        assert exc.value.args[0]['results'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['results'][0]['nameservers'] == [
            'ns.example.com',
        ]

    def test_single_ips(self):
        fake_query = MagicMock()
        fake_query.question = 'Doctor Who?'
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': 'ns.example.com',
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                    )),
                },
                {
                    'target': 'ns.example.com',
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1:2::3'),
                    )),
                },
            ],
        })
        udp_sequence = [
            {
                'query_target': dns.name.from_unicode(u'com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'www.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'www.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                ), dns.rrset.from_rdata(
                    'www.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'example.org')
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with pytest.raises(AnsibleExitJson) as exc:
                        with set_module_args({
                            'name': ['www.example.com'],
                            'resolve_addresses': True,
                        }):
                            nameserver_info.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert len(exc.value.args[0]['results']) == 1
        assert exc.value.args[0]['results'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['results'][0]['nameservers'] == [
            '1:2::3',
            '3.3.3.3',
        ]

    def test_timeout(self):
        fake_query = MagicMock()
        fake_query.question = 'Doctor Who?'
        resolver = mock_resolver(['1.1.1.1'], {})
        udp_sequence = [
            {
                'query_target': dns.name.from_unicode(u'com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'www.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'raise': dns.exception.Timeout(timeout=9),
            },
            {
                'query_target': dns.name.from_unicode(u'www.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                    'www.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'mail.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'raise': dns.exception.Timeout(timeout=9),
            },
            {
                'query_target': dns.name.from_unicode(u'mail.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 9,
                },
                'raise': dns.exception.Timeout(timeout=9),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with pytest.raises(AnsibleFailJson) as exc:
                        with set_module_args({
                            'name': ['www.example.com', 'mail.example.com'],
                            'query_timeout': 9,
                            'query_retry': 1,
                        }):
                            nameserver_info.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['msg'] in (
            'Unexpected DNS error: The DNS operation timed out after 9 seconds',
            'Unexpected DNS error: The DNS operation timed out after 9.000 seconds',
        )
        assert len(exc.value.args[0]['results']) == 2
        assert exc.value.args[0]['results'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['results'][0]['nameservers'] == ['ns.example.com']
        assert exc.value.args[0]['results'][1]['name'] == 'mail.example.com'
        assert 'nameservers' not in exc.value.args[0]['results'][1]

    def test_nxdomain(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': 'ns.example.com',
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                    )),
                },
                {
                    'target': 'ns.example.com',
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1:2::3'),
                    )),
                },
            ],
            ('1:2::3', '3.3.3.3'): [
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                },
            ],
        })
        udp_sequence = [
            {
                'query_target': dns.name.from_unicode(u'com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NXDOMAIN),
            },
            {
                'query_target': dns.name.from_unicode(u'example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'www.example.com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NXDOMAIN),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with pytest.raises(AnsibleExitJson) as exc:
                        with set_module_args({
                            'name': ['www.example.com'],
                        }):
                            nameserver_info.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert len(exc.value.args[0]['results']) == 1
        assert exc.value.args[0]['results'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['results'][0]['nameservers'] == ['ns.example.com']

    def test_servfail(self):
        resolver = mock_resolver(['1.1.1.1'], {})
        udp_sequence = [
            {
                'query_target': dns.name.from_unicode(u'com'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.SERVFAIL),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with pytest.raises(AnsibleFailJson) as exc:
                        with set_module_args({
                            'name': ['www.example.com'],
                        }):
                            nameserver_info.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['msg'] == 'Unexpected resolving error: Error SERVFAIL while querying 1.1.1.1 with query get NS for "com."'
        assert len(exc.value.args[0]['results']) == 1
        assert exc.value.args[0]['results'][0]['name'] == 'www.example.com'
        assert 'nameservers' not in exc.value.args[0]['results'][0]
