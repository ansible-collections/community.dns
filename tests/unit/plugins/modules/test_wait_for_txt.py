# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.modules import wait_for_txt
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


def mock_sleep(delay):
    pass


def mock_monotonic(call_sequence):
    def f():
        assert len(call_sequence) > 0, 'monotonic() was called more often than expected'
        value = call_sequence[0]
        del call_sequence[0]
        return value

    return f


class TestWaitForTXT(ModuleTestCase):
    def test_single(self):
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
                {
                    'target': 'ns.example.org',
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '4.4.4.4'),
                    )),
                },
                {
                    'target': 'ns.example.org',
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('1:2::3', '3.3.3.3'): [
                {
                    'target': dns.name.from_unicode(u'example.org'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
                    )),
                },
            ],
            ('4.4.4.4', ): [
                {
                    'target': dns.name.from_unicode(u'example.org'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
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
            {
                'query_target': dns.name.from_unicode(u'org'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'org',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.org'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'example.org'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.org',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.org'),
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'www.example.com',
                                        'values': [
                                            'asdf',
                                        ]
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['asdf'],
            'ns.example.org': ['asdf'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 1

    def test_double(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'fdsa'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'mail.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'mail.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"any bar"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'fdsa'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
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
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                    'mail.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'www.example.com',
                                        'values': [
                                            'asdf',
                                        ],
                                        'mode': 'equals',
                                    },
                                    {
                                        'name': 'mail.example.com',
                                        'values': [
                                            'foo bar',
                                            'any bar',
                                        ],
                                        'mode': 'superset',
                                    },
                                ],
                                'timeout': 10,
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 2
        assert len(exc.value.args[0]['records']) == 2
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['asdf'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 3
        assert exc.value.args[0]['records'][1]['name'] == 'mail.example.com'
        assert exc.value.args[0]['records'][1]['done'] is True
        assert exc.value.args[0]['records'][1]['values'] == {
            'ns.example.com': ['any bar'],
        }
        assert exc.value.args[0]['records'][1]['check_count'] == 1

    def test_subset(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'as df'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"another one"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"foo bar"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"another one"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"foo bar"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"another one"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'as df'),
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
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'example.com',
                                        'values': [
                                            'asdf',
                                            'asdf',
                                            'foo bar',
                                        ],
                                        'mode': 'subset',
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['foo bar', 'another one', 'asdf'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 3

    def test_superset(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'mail.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'fdsa'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf ""'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bee'),
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
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                    'mail.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'www.example.com',
                                        'values': [
                                            'asdf',
                                            'bee',
                                        ],
                                        'mode': 'superset',
                                    },
                                    {
                                        'name': 'mail.example.com',
                                        'values': [
                                            'foo bar',
                                            'any bar',
                                        ],
                                        'mode': 'superset',
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 2
        assert len(exc.value.args[0]['records']) == 2
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['asdf', 'bee'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 3
        assert exc.value.args[0]['records'][1]['name'] == 'mail.example.com'
        assert exc.value.args[0]['records'][1]['done'] is True
        assert exc.value.args[0]['records'][1]['values'] == {
            'ns.example.com': [],
        }
        assert exc.value.args[0]['records'][1]['check_count'] == 1

    def test_superset_not_empty(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bumble'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bee'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'wizard'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bumble'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bee'),
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
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'example.com',
                                        'values': [
                                            'bumble',
                                            'bee',
                                        ],
                                        'mode': 'superset_not_empty',
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['bumble', 'bee'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 4

    def test_equals(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bumble bee'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'wizard'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'wizard'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'foo'),
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
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'example.com',
                                        'values': [
                                            'foo',
                                            'bumble bee',
                                            'wizard',
                                        ],
                                        'mode': 'equals',
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['bumble bee', 'wizard', 'foo'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 4

    def test_equals_ordered(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'wizard'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'foo'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'foo'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"bumble bee"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'wizard'),
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
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleExitJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'example.com',
                                        'values': [
                                            'foo',
                                            'bumble bee',
                                            'wizard',
                                        ],
                                        'mode': 'equals_ordered',
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['changed'] is False
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'example.com'
        assert exc.value.args[0]['records'][0]['done'] is True
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['foo', 'bumble bee', 'wizard'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 4

    def test_timeout(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'fdsa'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'mail.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'mail.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"any bar"'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'fdsa'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdf'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'asdfasdf'),
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
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                    'mail.example.com',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.com. 12345 7200 120 2419200 10800'),
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with patch('ansible_collections.community.dns.plugins.modules.wait_for_txt.monotonic',
                                   mock_monotonic([0, 0.01, 1.2, 6.013, 7.41, 12.021])):
                            with pytest.raises(AnsibleFailJson) as exc:
                                with set_module_args({
                                    'records': [
                                        {
                                            'name': 'www.example.com',
                                            'values': [
                                                'asdf',
                                            ],
                                            'mode': 'equals',
                                        },
                                        {
                                            'name': 'mail.example.com',
                                            'values': [
                                                'foo bar',
                                                'any bar',
                                            ],
                                            'mode': 'superset',
                                        },
                                    ],
                                    'timeout': 12,
                                }):
                                    wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['msg'] == 'Timeout (1 out of 2 check(s) passed).'
        assert exc.value.args[0]['completed'] == 1
        assert len(exc.value.args[0]['records']) == 2
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is False
        assert exc.value.args[0]['records'][0]['values'] == {
            'ns.example.com': ['asdfasdf'],
        }
        assert exc.value.args[0]['records'][0]['check_count'] == 3
        assert exc.value.args[0]['records'][1]['name'] == 'mail.example.com'
        assert exc.value.args[0]['records'][1]['done'] is True
        assert exc.value.args[0]['records'][1]['values'] == {
            'ns.example.com': ['any bar'],
        }
        assert exc.value.args[0]['records'][1]['check_count'] == 1

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
                    with patch('time.sleep', mock_sleep):
                        with patch('ansible_collections.community.dns.plugins.modules.wait_for_txt.monotonic',
                                   mock_monotonic([0, 0.01, 1.2, 6.013])):
                            with pytest.raises(AnsibleFailJson) as exc:
                                with set_module_args({
                                    'records': [
                                        {
                                            'name': 'www.example.com',
                                            'values': [
                                                'asdf',
                                            ],
                                        },
                                    ],
                                    'timeout': 2,
                                }):
                                    wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['failed'] is True
        assert exc.value.args[0]['msg'] == 'Timeout (0 out of 1 check(s) passed).'
        assert exc.value.args[0]['completed'] == 0
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is False
        assert len(exc.value.args[0]['records'][0]['values']) == 1
        assert exc.value.args[0]['records'][0]['values']['ns.example.com'] == []
        assert exc.value.args[0]['records'][0]['check_count'] == 2

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
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleFailJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'www.example.com',
                                        'values': [
                                            'asdf',
                                        ],
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['msg'] == 'Unexpected resolving error: Error SERVFAIL while querying 1.1.1.1 with query get NS for "com."'
        assert exc.value.args[0]['completed'] == 0
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is False
        assert 'values' not in exc.value.args[0]['records'][0]
        assert exc.value.args[0]['records'][0]['check_count'] == 0

    def test_cname_loop(self):
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
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
                {
                    'target': 'ns.example.org',
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '4.4.4.4'),
                    )),
                },
                {
                    'target': 'ns.example.org',
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'raise': dns.resolver.NoAnswer(response=fake_query),
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
            {
                'query_target': dns.name.from_unicode(u'org'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'org',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.org'),
                )]),
            },
            {
                'query_target': dns.name.from_unicode(u'example.org'),
                'query_type': dns.rdatatype.NS,
                'nameserver': '1.1.1.1',
                'kwargs': {
                    'timeout': 10,
                },
                'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                    'example.org',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.org'),
                ), dns.rrset.from_rdata(
                    'example.org',
                    3600,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'www.example.com')
                )]),
            },
        ]
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                    with patch('time.sleep', mock_sleep):
                        with pytest.raises(AnsibleFailJson) as exc:
                            with set_module_args({
                                'records': [
                                    {
                                        'name': 'www.example.com',
                                        'values': [
                                            'asdf',
                                        ],
                                    },
                                ],
                            }):
                                wait_for_txt.main()

        print(exc.value.args[0])
        assert exc.value.args[0]['msg'] == 'Unexpected resolving error: Found CNAME loop starting at www.example.com'
        assert exc.value.args[0]['completed'] == 0
        assert len(exc.value.args[0]['records']) == 1
        assert exc.value.args[0]['records'][0]['name'] == 'www.example.com'
        assert exc.value.args[0]['records'][0]['done'] is False
        assert 'values' not in exc.value.args[0]['records'][0]
        assert exc.value.args[0]['records'][0]['check_count'] == 0
