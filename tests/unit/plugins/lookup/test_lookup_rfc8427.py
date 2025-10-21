# -*- coding: utf-8 -*-
# Copyright (c) 2023-2025, Felix Fontein <felix@fontein.de>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import json

import pytest
from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    patch,
)
from ansible_collections.community.internal_test_tools.tests.unit.compat.unittest import (
    TestCase,
)
from dns.rdataclass import to_text

from ..module_utils.resolver_helper import (
    create_mock_answer,
    mock_query_udp,
    mock_resolver,
)


dns = pytest.importorskip("dns")


class TestLookupRFC8427(TestCase):
    def setUp(self) -> None:
        self.lookup = lookup_loader.get("community.dns.lookup_rfc8427")

    def test_rfc8427_json_correctness(self) -> None:
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

        assert isinstance(result, list)
        assert len(result) == 1
        msg = result[0]

        # Ensure JSON serializable
        json.dumps(msg)  # No exception

        # Header validation (RFC 8427 Section 4.1)
        header = msg["Header"]
        assert isinstance(header, dict)
        assert "id" in header and isinstance(header["id"], int)
        assert (
            "flags" in header
            and isinstance(header["flags"], list)
            and all(isinstance(f, str) for f in header["flags"])
        )
        assert "rcode" in header and isinstance(header["rcode"], str)  # e.g., "NOERROR"
        assert "question_count" in header and isinstance(header["question_count"], int)
        assert "answer_count" in header and isinstance(header["answer_count"], int)
        assert "authority_count" in header and isinstance(
            header["authority_count"], int
        )
        assert "additional_count" in header and isinstance(
            header["additional_count"], int
        )

        # Question validation (RFC 8427 Section 4.2)
        question = msg["Question"]
        assert isinstance(question, list)
        assert len(question) == 1
        q = question[0]
        assert isinstance(q, dict)
        assert (
            "name" in q
            and isinstance(q["name"], str)
            and q["name"] == "www.example.com"
        )
        assert (
            "type" in q and isinstance(q["type"], int) and q["type"] == dns.rdatatype.A
        )
        assert (
            "class" in q
            and isinstance(q["class"], str)
            and q["class"] == to_text(dns.rdataclass.IN)
        )

        # Answer validation (RFC 8427 Section 4.3; similar for Authority/Additional)
        answer = msg["Answer"]
        assert isinstance(answer, list)
        assert len(answer) == 1
        rr = answer[0]
        assert isinstance(rr, dict)
        assert (
            "name" in rr
            and isinstance(rr["name"], str)
            and rr["name"] == "www.example.com"
        )
        assert (
            "type" in rr
            and isinstance(rr["type"], int)
            and rr["type"] == dns.rdatatype.A
        )
        assert (
            "class" in rr
            and isinstance(rr["class"], str)
            and rr["class"] == to_text(dns.rdataclass.IN)
        )
        assert "ttl" in rr and isinstance(rr["ttl"], int) and rr["ttl"] == 300
        assert (
            "data" in rr and isinstance(rr["data"], str) and rr["data"] == "127.0.0.1"
        )  # A record specific

        # Authority and Additional should be empty lists
        assert msg["Authority"] == []
        assert msg["Additional"] == []

        # Test with MX for complex data object (add another query mock if needed)
        mx_rrset = dns.rrset.from_rdata(
            "example.com",
            3600,
            dns.rdata.from_text(
                dns.rdataclass.IN, dns.rdatatype.MX, "10 mail.example.com"
            ),
        )
        resolver_mx = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("example.com", origin=None),
                        "search": True,
                        "rdtype": dns.rdatatype.MX,
                        "lifetime": 10,
                        "result": create_mock_answer(mx_rrset),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver_mx):
            with patch("dns.resolver.Resolver", resolver_mx):
                with patch("dns.query.udp", mock_query_udp([])):
                    result_mx = self.lookup.run(["example.com"], type="MX")

        msg_mx = result_mx[0]

        # Question validation for MX (RFC 8427 Section 4.2)
        question_mx = msg_mx["Question"]
        assert isinstance(question_mx, list)
        assert len(question_mx) == 1
        q_mx = question_mx[0]
        assert isinstance(q_mx, dict)
        assert (
            "name" in q_mx
            and isinstance(q_mx["name"], str)
            and q_mx["name"] == "example.com"
        )
        assert (
            "type" in q_mx
            and isinstance(q_mx["type"], int)
            and q_mx["type"] == dns.rdatatype.MX
        )
        assert (
            "class" in q_mx
            and isinstance(q_mx["class"], str)
            and q_mx["class"] == to_text(dns.rdataclass.IN)
        )

        # Answer validation for MX
        answer_mx = msg_mx["Answer"]
        assert isinstance(answer_mx, list)
        assert len(answer_mx) == 1
        mx_rr = answer_mx[0]
        assert isinstance(mx_rr, dict)
        assert (
            "name" in mx_rr
            and isinstance(mx_rr["name"], str)
            and mx_rr["name"] == "example.com"
        )
        assert (
            "type" in mx_rr
            and isinstance(mx_rr["type"], int)
            and mx_rr["type"] == dns.rdatatype.MX
        )
        assert (
            "class" in mx_rr
            and isinstance(mx_rr["class"], str)
            and mx_rr["class"] == to_text(dns.rdataclass.IN)
        )
        assert "ttl" in mx_rr and isinstance(mx_rr["ttl"], int) and mx_rr["ttl"] == 3600
        assert isinstance(mx_rr["data"], dict)  # MX data as object
        assert (
            "preference" in mx_rr["data"]
            and isinstance(mx_rr["data"]["preference"], int)
            and mx_rr["data"]["preference"] == 10
        )
        assert (
            "exchange" in mx_rr["data"]
            and isinstance(mx_rr["data"]["exchange"], str)
            and mx_rr["data"]["exchange"] == "mail.example.com"
        )

        # Authority and Additional should be empty lists for MX too
        assert msg_mx["Authority"] == []
        assert msg_mx["Additional"] == []

    def test_rfc8427_simple(self) -> None:
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

        assert isinstance(result, list)
        assert len(result) == 1
        msg = result[0]

        # check for RFC 8427 fields
        assert "Header" in msg
        assert "Question" in msg
        assert "Answer" in msg
        assert "Authority" in msg
        assert "Additional" in msg

        # check for Answer content
        answer = msg["Answer"]
        assert isinstance(answer, list)
        assert answer[0]["name"] == "www.example.com"  # no trailing dot
        assert answer[0]["type"] == dns.rdatatype.A
        assert answer[0]["data"] == "127.0.0.1"

    def test_rfc8427_nxdomain_empty(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "nope.example.com", origin=None
                        ),
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
                    result = self.lookup.run(["nope.example.com"])

        assert isinstance(result, list)
        assert len(result) == 1
        msg = result[0]
        assert msg["Answer"] == []

    def test_rfc8427_nxdomain_fail(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "nope.example.com", origin=None
                        ),
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
                    with pytest.raises(AnsibleLookupError):
                        self.lookup.run(["nope.example.com"], nxdomain_handling="fail")

    def test_rfc8427_servfail_exhaustion(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode("example.com", origin=None),
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
                    with pytest.raises(AnsibleLookupError):
                        self.lookup.run(
                            ["example.com"], servfail_retries=0
                        )  # Exhaust immediately

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
        assert result[0]["Answer"] == [
            {
                "class": "IN",
                "data": "::1",
                "name": "example.org",
                "ttl": 300,
                "type": 28,
            },
        ]

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
