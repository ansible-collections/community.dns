# -*- coding: utf-8 -*-
# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader

from ansible_collections.community.internal_test_tools.tests.unit.compat.unittest import TestCase
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import patch, MagicMock

from ..module_utils.resolver_helper import (
    mock_resolver,
    mock_query_udp,
    create_mock_answer,
)

# We need dnspython
dns = pytest.importorskip('dns')


class TestLookupAsDict(TestCase):
    def setUp(self):
        self.lookup = lookup_loader.get("community.dns.lookup_as_dict")

    def test_simple(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.1'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.2'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['www.example.com'])

        print(result)
        assert len(result) == 2
        assert result[0] == {
            'address': '127.0.0.1',
        }
        assert result[1] == {
            'address': '127.0.0.2',
        }

    def test_no_search(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com'),
                    'search': False,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.1'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.2'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['www.example.com'], search=False)

        print(result)
        assert len(result) == 2
        assert result[0] == {
            'address': '127.0.0.1',
        }
        assert result[1] == {
            'address': '127.0.0.2',
        }

    def test_retry_success(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'www.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.1'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '127.0.0.2'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['www.example.com'])

        print(result)
        assert len(result) == 2
        assert result[0] == {
            'address': '127.0.0.1',
        }
        assert result[1] == {
            'address': '127.0.0.2',
        }

    def test_retry_fail(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'raise': dns.exception.Timeout(timeout=10),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'])

        print(exc.value.args[0])
        assert exc.value.args[0].startswith('Unexpected DNS error for www.example.com: The DNS operation timed out after 10')

    def test_simple_nxdomain_empty(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['www.example.com'], nxdomain_handling='empty')

        print(result)
        assert len(result) == 0

    def test_simple_nxdomain_fail(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'], nxdomain_handling='fail')

        print(exc.value.args[0])
        assert exc.value.args[0] == 'Got NXDOMAIN when querying www.example.com'

    def test_simple_servfail(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'])

        print(exc.value.args[0])
        assert exc.value.args[0] == "Unexpected resolving error for www.example.com: Error SERVFAIL while querying ['1.1.1.1']"

    def test_retry_servfail_success(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['www.example.com'], servfail_retries=2)

        print(result)
        assert len(result) == 0

    def test_retry_servfail_fail(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
                {
                    'target': dns.name.from_unicode(u'www.example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'], servfail_retries=2)

        print(exc.value.args[0])
        assert exc.value.args[0] == "Unexpected resolving error for www.example.com: Error SERVFAIL while querying ['1.1.1.1']"

    def test_type(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'example.com', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.TXT,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, '"foo bar"'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'baz bam'),
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, 'bar'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['example.com'], type='TXT')

        print(result)
        assert len(result) == 3
        assert result[0] == {
            'strings': ['foo bar'],
            'value': 'foo bar',
        }
        assert result[1] == {
            'strings': ['baz', 'bam'],
            'value': 'bazbam',
        }
        assert result[2] == {
            'strings': ['bar'],
            'value': 'bar',
        }

    def test_server(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('2.2.2.2', '3.3.3.3'): [
                {
                    'target': dns.name.from_unicode(u'example.org', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '::1'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['example.org'], type='AAAA', server=['2.2.2.2', '3.3.3.3'])

        print(result)
        assert len(result) == 1
        assert result[0] == {
            'address': '::1',
        }

    def test_server_resolve(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '1.2.3.4'),
                    )),
                },
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'ns.example.com',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1::2'),
                    )),
                },
            ],
            ('1.2.3.4', '1::2', '2.2.2.2', '3.3.3.3'): [
                {
                    'target': dns.name.from_unicode(u'example.org', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 10,
                    'result': create_mock_answer(dns.rrset.from_rdata(
                        'example.org',
                        300,
                        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '::1'),
                    )),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(['example.org'], type='AAAA', server=['2.2.2.2', 'ns.example.com', '3.3.3.3'])

        print(result)
        assert len(result) == 1
        assert result[0] == {
            'address': '::1',
        }

    def test_server_resolve_nxdomain(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'], server=['2.2.2.2', 'ns.example.com'])

        print(exc.value.args[0])
        assert exc.value.args[0] == 'Unexpected DNS error for ns.example.com: The DNS query name does not exist: ns.example.com.'

    def test_server_resolve_servfail(self):
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 10,
                    'result': create_mock_answer(rcode=dns.rcode.SERVFAIL),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(['www.example.com'], server=['2.2.2.2', 'ns.example.com'])

        print(exc.value.args[0])
        assert exc.value.args[0] == "Unexpected resolving error for ns.example.com: Error SERVFAIL while querying ['1.1.1.1']"

    def test_server_resolve_empty_lifetime(self):
        fake_query = MagicMock()
        fake_query.question = 'Doctor Who?'
        resolver = mock_resolver(['1.1.1.1'], {
            ('1.1.1.1', ): [
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.A,
                    'lifetime': 5,
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
                {
                    'target': dns.name.from_unicode(u'ns.example.com'),
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 5,
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
            ('3.3.3.3', ): [
                {
                    'target': dns.name.from_unicode(u'example.org', origin=None),
                    'search': True,
                    'rdtype': dns.rdatatype.AAAA,
                    'lifetime': 5,
                    'raise': dns.resolver.NoAnswer(response=fake_query),
                },
            ],
        })
        with patch('dns.resolver.get_default_resolver', resolver):
            with patch('dns.resolver.Resolver', resolver):
                with patch('dns.query.udp', mock_query_udp([])):
                    result = self.lookup.run(
                        ['example.org'],
                        type='AAAA',
                        server=['ns.example.com', '3.3.3.3'],
                        query_timeout=5,
                    )

        print(result)
        assert len(result) == 0
