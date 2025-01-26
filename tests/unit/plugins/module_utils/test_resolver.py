# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils import resolver
from ansible_collections.community.dns.plugins.module_utils.resolver import (
    ResolveDirectlyFromNameServers,
    ResolverError,
    assert_requirements_present,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
    patch,
)

from .resolver_helper import (
    create_mock_answer,
    create_mock_response,
    mock_query_udp,
    mock_resolver,
)


# We need dnspython
dns = pytest.importorskip('dns')


def test_assert_requirements_present():
    class ModuleFailException(Exception):
        pass

    class FakeModule(object):
        def fail_json(self, **kwargs):
            raise ModuleFailException(kwargs)

    module = FakeModule()

    orig_importerror = resolver.DNSPYTHON_IMPORTERROR
    try:
        resolver.DNSPYTHON_IMPORTERROR = None
        assert_requirements_present(module)

        resolver.DNSPYTHON_IMPORTERROR = 'asdf'
        with pytest.raises(ModuleFailException) as exc:
            assert_requirements_present(module)

        assert 'dnspython' in exc.value.args[0]['msg']
        assert 'asdf' == exc.value.args[0]['exception']

    finally:
        resolver.DNSPYTHON_IMPORTERROR = orig_importerror


def test_lookup_ns_names():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
    udp_sequence = [
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
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.org.'),
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com.'),
            )]),
        },
        {
            'query_target': dns.name.from_unicode(u'example.com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '3.3.3.3',
            'kwargs': {
                'timeout': 10,
            },
            'result': create_mock_response(dns.rcode.NOERROR, answer=[dns.rrset.from_rdata(
                'example.com',
                60,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'foo.bar.'),
            )], authority=[dns.rrset.from_rdata(
                'example.com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com.'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers(always_ask_default_resolver=False)
                # Use default resolver
                ns, cname = resolver_instance._lookup_ns_names(dns.name.from_unicode(u'example.com'))
                assert ns == ['ns.example.com.', 'ns.example.org.']
                assert cname is None
                # Provide nameserver IPs
                ns, cname = resolver_instance._lookup_ns_names(dns.name.from_unicode(u'example.com'), nameserver_ips=['3.3.3.3', '1.1.1.1'])
                assert ns == ['ns.example.com.']
                assert cname == dns.name.from_unicode(u'foo.bar.')
                # Provide empty nameserver list
                with pytest.raises(ResolverError) as exc:
                    resolver_instance._lookup_ns_names(dns.name.from_unicode(u'example.com'), nameservers=[])
                assert exc.value.args[0] == 'Have neither nameservers nor nameserver IPs'


def test_resolver():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
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
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '2:3::4'),
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
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
        ],
        ('1:2::3', '2:3::4', '3.3.3.3'): [
            {
                'target': dns.name.from_unicode(u'example.org'),
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'example.org',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '1.2.3.4'),
                )),
            },
        ],
        ('4.4.4.4', ): [
            {
                'target': dns.name.from_unicode(u'example.org'),
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'example.org',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '1.2.3.5'),
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
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['1:2::3', '2:3::4', '3.3.3.3']
                # www.example.com is a CNAME for example.org
                rrset_dict = resolver_instance.resolve('www.example.com')
                assert sorted(rrset_dict.keys()) == ['ns.example.com', 'ns.example.org']
                rrset = rrset_dict['ns.example.com']
                assert len(rrset) == 1
                assert rrset.name == dns.name.from_unicode(u'example.org', origin=None)
                assert rrset.rdtype == dns.rdatatype.A
                assert rrset[0].to_text() == u'1.2.3.4'
                rrset = rrset_dict['ns.example.org']
                assert len(rrset) == 1
                assert rrset.name == dns.name.from_unicode(u'example.org', origin=None)
                assert rrset.rdtype == dns.rdatatype.A
                assert rrset[0].to_text() == u'1.2.3.5'
                # The following results should be cached:
                assert resolver_instance.resolve_nameservers('com', resolve_addresses=True) == ['2.2.2.2']
                assert resolver_instance.resolve_nameservers('org') == ['ns.org']
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.example.com']
                assert resolver_instance.resolve_nameservers('example.org') == ['ns.example.com', 'ns.example.org']


def test_timeout_handling():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'raise': dns.exception.Timeout(timeout=10),
            },
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
                'raise': dns.exception.Timeout(timeout=10),
            },
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'raise': dns.exception.Timeout(timeout=10),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'raise': dns.exception.Timeout(timeout=10),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.com',
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
            'raise': dns.exception.Timeout(timeout=10),
        },
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
            'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                'example.com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']
                # The following results should be cached:
                assert resolver_instance.resolve_nameservers('com') == ['ns.com']
                assert resolver_instance.resolve_nameservers('com', resolve_addresses=True) == ['2.2.2.2']
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.example.com']
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']


def test_timeout_failure():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
    udp_sequence = [
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'raise': dns.exception.Timeout(timeout=1),
        },
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'raise': dns.exception.Timeout(timeout=2),
        },
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'raise': dns.exception.Timeout(timeout=3),
        },
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'raise': dns.exception.Timeout(timeout=4),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                with pytest.raises(dns.exception.Timeout) as exc:
                    resolver_instance = ResolveDirectlyFromNameServers()
                    resolver_instance.resolve_nameservers('example.com')
                assert exc.value.kwargs['timeout'] == 4


def test_error_nameserver_nxdomain_none():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
            'result': create_mock_response(dns.rcode.NXDOMAIN),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                assert resolver_instance.resolve_nameservers('example.com') == []


def test_error_nameserver_nxdomain_partial_first():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
            'result': create_mock_response(dns.rcode.NXDOMAIN),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.com']


def test_error_nameserver_nxdomain_partial_second():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
                'com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.com']


def test_error_nxdomain_ok():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                )),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1:2::3'),
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '2:3::4'),
                )),
            },
        ],
        ('1:2::3', '2:3::4', '3.3.3.3'): [
            {
                'target': dns.name.from_unicode(u'example.com'),
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
            'result': create_mock_response(dns.rcode.NXDOMAIN),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                rrset_dict = resolver_instance.resolve('example.com', nxdomain_is_empty=True)
                print(rrset_dict)
                assert sorted(rrset_dict.keys()) == ['ns.com']
                assert rrset_dict['ns.com'] == []


def test_error_nxdomain_fail():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                )),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1:2::3'),
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '2:3::4'),
                )),
            },
        ],
        ('1:2::3', '2:3::4', '3.3.3.3'): [
            {
                'target': dns.name.from_unicode(u'example.com'),
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
            'result': create_mock_response(dns.rcode.NXDOMAIN),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                with pytest.raises(dns.resolver.NXDOMAIN) as exc:
                    resolver_instance.resolve('example.com', nxdomain_is_empty=False)
                print(exc.value.args[0])
                assert exc.value.args[0] == 'The DNS query name does not exist: example.com.'


def test_error_servfail():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                with pytest.raises(ResolverError) as exc:
                    resolver_instance = ResolveDirectlyFromNameServers()
                    resolver_instance.resolve_nameservers('example.com')
                assert exc.value.args[0] == 'Error SERVFAIL while querying 1.1.1.1 with query get NS for "com."'


def test_error_servfail_retry_success():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'result': create_mock_response(dns.rcode.SERVFAIL),
        },
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                'com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers(servfail_retries=2)
                assert resolver_instance.resolve_nameservers('com') == ['ns.com']


def test_error_servfail_retry_fail():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {})
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
        {
            'query_target': dns.name.from_unicode(u'com'),
            'query_type': dns.rdatatype.NS,
            'nameserver': '1.1.1.1',
            'kwargs': {
                'timeout': 10,
            },
            'result': create_mock_response(dns.rcode.SERVFAIL),
        },
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
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                with pytest.raises(ResolverError) as exc:
                    resolver_instance = ResolveDirectlyFromNameServers(servfail_retries=2)
                    resolver_instance.resolve_nameservers('example.com')
                assert exc.value.args[0] == 'Error SERVFAIL while querying 1.1.1.1 with query get NS for "com."'


def test_servfail_handling():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
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
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.com',
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
            'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                'example.com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers(servfail_retries=2)
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']
                # The following results should be cached:
                assert resolver_instance.resolve_nameservers('com') == ['ns.com']
                assert resolver_instance.resolve_nameservers('com', resolve_addresses=True) == ['2.2.2.2']
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.example.com']
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']


def test_servfail_failing():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
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
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
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
            'result': create_mock_response(dns.rcode.NOERROR, authority=[dns.rrset.from_rdata(
                'example.com',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers(servfail_retries=2)
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']
                # The following results should be cached:
                assert resolver_instance.resolve_nameservers('com') == ['ns.com']
                with pytest.raises(ResolverError) as exc:
                    resolver_instance.resolve_nameservers('com', resolve_addresses=True)
                assert exc.value.args[0] == "Error SERVFAIL while querying ['1.1.1.1']"


def test_no_response():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.example.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '5.5.5.5'),
                )),
            },
            {
                'target': 'ns.example.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
            {
                'target': 'ns2.example.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.example.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '4.4.4.4'),
                )),
            },
            {
                'target': 'ns2.example.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
        ],
        ('3.3.3.3', '5.5.5.5'): [
            {
                'target': dns.name.from_unicode(u'example.com'),
                'lifetime': 10,
                'result': create_mock_answer(),
            },
        ],
        ('4.4.4.4', ): [
            {
                'target': dns.name.from_unicode(u'example.com'),
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
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns2.example.com'),
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                rrset_dict = resolver_instance.resolve('example.com')
                assert sorted(rrset_dict.keys()) == ['ns.example.com', 'ns2.example.com']
                assert rrset_dict['ns.example.com'] is None
                assert rrset_dict['ns2.example.com'] is None
                # Verify nameserver IPs
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.example.com', 'ns2.example.com']
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3', '4.4.4.4', '5.5.5.5']


def test_cname_loop():
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.com',
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.example.com',
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.example.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
                )),
            },
            {
                'target': 'ns.org',
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.3.3'),
                )),
            },
            {
                'target': 'ns.example.org',
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.example.org',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '4.4.4.4'),
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
            ), dns.rrset.from_rdata(
                'example.org',
                3600,
                dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'www.example.com')
            )]),
        },
    ]
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers()
                with pytest.raises(ResolverError) as exc:
                    resolver_instance.resolve('www.example.com')
                assert exc.value.args[0] == 'Found CNAME loop starting at www.example.com'


def test_resolver_non_default():
    fake_query = MagicMock()
    fake_query.question = 'Doctor Who?'
    mock_resolver_instance = mock_resolver(['1.1.1.1'], {
        ('1.1.1.1', ): [
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.2.2'),
                )),
            },
            {
                'target': 'ns.com',
                'rdtype': dns.rdatatype.AAAA,
                'lifetime': 10,
                'raise': dns.resolver.NoAnswer(response=fake_query),
            },
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
                'target': 'ns.org',
                'rdtype': dns.rdatatype.A,
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'ns.com',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '2.2.3.3'),
                )),
            },
            {
                'target': 'ns.org',
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
        ('3.3.3.3', ): [
            {
                'target': dns.name.from_unicode(u'example.org'),
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'example.org',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '1.2.3.4'),
                )),
            },
        ],
        ('4.4.4.4', ): [
            {
                'target': dns.name.from_unicode(u'example.org'),
                'lifetime': 10,
                'result': create_mock_answer(dns.rrset.from_rdata(
                    'example.org',
                    300,
                    dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '1.2.3.4'),
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
            'nameserver': '2.2.2.2',
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
            'nameserver': '3.3.3.3',
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
            'nameserver': '2.2.3.3',
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
    with patch('dns.resolver.get_default_resolver', mock_resolver_instance):
        with patch('dns.resolver.Resolver', mock_resolver_instance):
            with patch('dns.query.udp', mock_query_udp(udp_sequence)):
                resolver_instance = ResolveDirectlyFromNameServers(always_ask_default_resolver=False)
                assert resolver_instance.resolve_nameservers('example.com') == ['ns.example.com']
                # www.example.com is a CNAME for example.org
                rrset_dict = resolver_instance.resolve('www.example.com')
                assert sorted(rrset_dict.keys()) == ['ns.example.com', 'ns.example.org']
                rrset = rrset_dict['ns.example.com']
                assert len(rrset) == 1
                assert rrset.name == dns.name.from_unicode(u'example.org', origin=None)
                assert rrset.rdtype == dns.rdatatype.A
                assert rrset[0].to_text() == u'1.2.3.4'
                rrset = rrset_dict['ns.example.org']
                assert len(rrset) == 1
                assert rrset.name == dns.name.from_unicode(u'example.org', origin=None)
                assert rrset.rdtype == dns.rdatatype.A
                assert rrset[0].to_text() == u'1.2.3.4'
                # The following results should be cached:
                assert resolver_instance.resolve_nameservers('com') == ['ns.com']
                print(resolver_instance.resolve_nameservers('example.com', resolve_addresses=True))
                assert resolver_instance.resolve_nameservers('example.com', resolve_addresses=True) == ['3.3.3.3']
                print(resolver_instance.resolve_nameservers('example.org', resolve_addresses=True))
                assert resolver_instance.resolve_nameservers('example.org', resolve_addresses=True) == ['3.3.3.3', '4.4.4.4']
