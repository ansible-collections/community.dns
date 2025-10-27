# -*- coding: utf-8 -*-
# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest
from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.unittest import (
    TestCase,
)

from ..module_utils.resolver_helper import (
    create_mock_answer,
    mock_query_udp,
    mock_resolver,
)


# We need dnspython
dns = pytest.importorskip("dns")


class TestLookupAsDict(TestCase):
    def setUp(self):
        self.lookup = lookup_loader.get("community.dns.lookup_as_dict")

    def test_simple(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "www.example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.1"
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.2"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["www.example.com"])

        print(result)
        assert len(result) == 2
        assert result[0] == {
            "address": "127.0.0.1",
        }
        assert result[1] == {
            "address": "127.0.0.2",
        }

    def test_no_search(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com"),
                        "search": False,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "www.example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.1"
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.2"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["www.example.com"], search=False)

        print(result)
        assert len(result) == 2
        assert result[0] == {
            "address": "127.0.0.1",
        }
        assert result[1] == {
            "address": "127.0.0.2",
        }

    def test_retry_success(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "www.example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.1"
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "127.0.0.2"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["www.example.com"])

        print(result)
        assert len(result) == 2
        assert result[0] == {
            "address": "127.0.0.1",
        }
        assert result[1] == {
            "address": "127.0.0.2",
        }

    def test_retry_fail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "raise": dns.exception.Timeout(timeout=10),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["www.example.com"])

        print(exc.value.args[0])
        assert exc.value.args[0].startswith(
            "Unexpected DNS error for www.example.com: The DNS operation timed out after 10"
        )

    def test_simple_nxdomain_empty(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(
                        ["www.example.com"], nxdomain_handling="empty"
                    )

        print(result)
        assert len(result) == 0

    def test_simple_nxdomain_fail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["www.example.com"], nxdomain_handling="fail")

        print(exc.value.args[0])
        assert exc.value.args[0] == "Got NXDOMAIN when querying www.example.com"

    def test_simple_servfail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["www.example.com"])

        print(exc.value.args[0])
        assert (
            exc.value.args[0]
            == "Unexpected resolving error for www.example.com: Error SERVFAIL while querying ['1.1.1.1']"
        )

    def test_retry_servfail_success(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["www.example.com"], servfail_retries=2)

        print(result)
        assert len(result) == 0

    def test_retry_servfail_fail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                    {
                        "target": dns.name.from_unicode("www.example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["www.example.com"], servfail_retries=2)

        print(exc.value.args[0])
        assert (
            exc.value.args[0]
            == "Unexpected resolving error for www.example.com: Error SERVFAIL while querying ['1.1.1.1']"
        )

    def test_type(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.TXT,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.TXT, '"foo bar"'
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.TXT, "baz bam"
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.TXT, "bar"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["example.com"], type="TXT")

        print(result)
        assert len(result) == 3
        assert result[0] == {
            "strings": ["foo bar"],
            "value": "foo bar",
        }
        assert result[1] == {
            "strings": ["baz", "bam"],
            "value": "bazbam",
        }
        assert result[2] == {
            "strings": ["bar"],
            "value": "bar",
        }

    def test_server(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("2.2.2.2", "3.3.3.3"): [
                    {
                        "target": dns.name.from_unicode("example.org", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.AAAA,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "example.org",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.AAAA, "::1"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(
                        ["example.org"], type="AAAA", server=["2.2.2.2", "3.3.3.3"]
                    )

        print(result)
        assert len(result) == 1
        assert result[0] == {
            "address": "::1",
        }

    def test_server_resolve(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "ns.example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.A, "1.2.3.4"
                                ),
                            )
                        ),
                    },
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.AAAA,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "ns.example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.AAAA, "1::2"
                                ),
                            )
                        ),
                    },
                ],
                ("1.2.3.4", "1::2", "2.2.2.2", "3.3.3.3"): [
                    {
                        "target": dns.name.from_unicode("example.org", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.AAAA,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "example.org",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.AAAA, "::1"
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(
                        ["example.org"],
                        type="AAAA",
                        server=["2.2.2.2", "ns.example.com", "3.3.3.3"],
                    )

        print(result)
        assert len(result) == 1
        assert result[0] == {
            "address": "::1",
        }

    def test_server_resolve_nxdomain(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(
                            ["www.example.com"], server=["2.2.2.2", "ns.example.com"]
                        )

        print(exc.value.args[0])
        assert (
            exc.value.args[0]
            == "Nameserver ns.example.com does not exist (The DNS query name does not exist: ns.example.com.)"
        )

    def test_server_resolve_servfail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.SERVFAIL),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(
                            ["www.example.com"], server=["2.2.2.2", "ns.example.com"]
                        )

        print(exc.value.args[0])
        assert (
            exc.value.args[0]
            == "Unexpected resolving error for ns.example.com: Error SERVFAIL while querying ['1.1.1.1']"
        )

    def test_server_resolve_empty_lifetime(self) -> None:
        fake_query = MagicMock()
        fake_query.question = "Doctor Who?"
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.A,
                        "lifetime": 5,
                        "raise": dns.resolver.NoAnswer(response=fake_query),
                    },
                    {
                        "target": dns.name.from_unicode("ns.example.com"),
                        "rdtype": dns.rdatatype.AAAA,
                        "lifetime": 5,
                        "raise": dns.resolver.NoAnswer(response=fake_query),
                    },
                ],
                ("3.3.3.3",): [
                    {
                        "target": dns.name.from_unicode("example.org", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.AAAA,
                        "lifetime": 5,
                        "raise": dns.resolver.NoAnswer(response=fake_query),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(
                        ["example.org"],
                        type="AAAA",
                        server=["ns.example.com", "3.3.3.3"],
                        query_timeout=5,
                    )

        print(result)
        assert len(result) == 0

    def test_https(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.HTTPS,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    '1 . alpn="h2,h3"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    "2 foo",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    "3 foo port=53",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    "4 foo key667=hello",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    '5 foo key667="hello\\210qoo"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    '6 foo ipv6hint="2001:db8::1,2001:db8::53:1"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    "7 foo alpn=h2,h3-19 mandatory=ipv4hint,alpn ipv4hint=192.0.2.1",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    '8 foo alpn="f\\\\oo\\,bar,h2"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.HTTPS,
                                    "9 foo alpn=f\\\092oo\092,bar,h2",
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["example.com"], type="HTTPS")

        print(result)
        assert len(result) == 9
        assert result[0] == {
            "priority": 1,
            "target": ".",
            "params": {"alpn": ["aDI=", "aDM="]},
        }
        assert result[1] == {"priority": 2, "target": "foo", "params": {}}
        assert result[2] == {"priority": 3, "target": "foo", "params": {"port": 53}}
        assert result[3] == {
            "priority": 4,
            "target": "foo",
            "params": {"key667": "aGVsbG8="},
        }
        assert result[4] == {
            "priority": 5,
            "target": "foo",
            "params": {"key667": "aGVsbG/ScW9v"},
        }
        assert result[5] == {
            "priority": 6,
            "target": "foo",
            "params": {"ipv6hint": ["2001:db8::1", "2001:db8::53:1"]},
        }
        assert result[6] == {
            "priority": 7,
            "target": "foo",
            "params": {
                "alpn": ["aDI=", "aDMtMTk="],
                "mandatory": ["alpn", "ipv4hint"],
                "ipv4hint": ["192.0.2.1"],
            },
        }
        assert result[7] == {
            "priority": 8,
            "target": "foo",
            "params": {"alpn": ["Zm9v", "YmFy", "aDI="]},
        }
        assert result[8] == {
            "priority": 9,
            "target": "foo",
            "params": {"alpn": ["ZgA5Mm9vADky", "YmFy", "aDI="]},
        }

    def test_svcb(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.SVCB,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "example.com",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    '1 . alpn="h2,h3"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "2 foo",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "3 foo port=53",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "4 foo key667=hello",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    '5 foo key667="hello\\210qoo"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    '6 foo ipv6hint="2001:db8::1,2001:db8::53:1"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "7 foo alpn=h2,h3-19 mandatory=ipv4hint,alpn ipv4hint=192.0.2.1",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    '8 foo alpn="f\\\\oo\\,bar,h2"',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "9 foo alpn=f\\\092oo\092,bar,h2",
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    '10 . ech="AEX+DQBBSQAgACBuPcsDfK+zfZY0gE1U80ppEIny7ZVjHw+y2AiJFqsZBAAEAAEAAQASY292ZXIuZWNoLWxhYnMuY29tAAA="',
                                ),
                                dns.rdata.from_text(
                                    dns.rdataclass.IN,
                                    dns.rdatatype.SVCB,
                                    "11 . no-default-alpn alpn=h3",
                                ),
                            )
                        ),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["example.com"], type="SVCB")

        print(result)
        assert len(result) == 11
        assert result[0] == {
            "priority": 1,
            "target": ".",
            "params": {"alpn": ["aDI=", "aDM="]},
        }
        assert result[1] == {"priority": 2, "target": "foo", "params": {}}
        assert result[2] == {"priority": 3, "target": "foo", "params": {"port": 53}}
        assert result[3] == {
            "priority": 4,
            "target": "foo",
            "params": {"key667": "aGVsbG8="},
        }
        assert result[4] == {
            "priority": 5,
            "target": "foo",
            "params": {"key667": "aGVsbG/ScW9v"},
        }
        assert result[5] == {
            "priority": 6,
            "target": "foo",
            "params": {"ipv6hint": ["2001:db8::1", "2001:db8::53:1"]},
        }
        assert result[6] == {
            "priority": 7,
            "target": "foo",
            "params": {
                "alpn": ["aDI=", "aDMtMTk="],
                "mandatory": ["alpn", "ipv4hint"],
                "ipv4hint": ["192.0.2.1"],
            },
        }
        assert result[7] == {
            "priority": 8,
            "target": "foo",
            "params": {"alpn": ["Zm9v", "YmFy", "aDI="]},
        }
        assert result[8] == {
            "priority": 9,
            "target": "foo",
            "params": {"alpn": ["ZgA5Mm9vADky", "YmFy", "aDI="]},
        }
        assert result[9] == {
            "priority": 10,
            "target": ".",
            "params": {
                "ech": "AEX+DQBBSQAgACBuPcsDfK+zfZY0gE1U80ppEIny7ZVjHw+y2AiJFqsZBAAEAAEAAQASY292ZXIuZWNoLWxhYnMuY29tAAA="
            },
        }
        assert result[10] == {
            "priority": 11,
            "target": ".",
            "params": {"no-default-alpn": None, "alpn": ["aDM="]},
        }
