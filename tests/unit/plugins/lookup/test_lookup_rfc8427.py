# -*- coding: utf-8 -*-
# Copyright (c) 2023-2025, Felix Fontein <felix@fontein.de>
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest
from ansible.errors import AnsibleLookupError
from ansible.plugins.loader import lookup_loader
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
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

dns = pytest.importorskip("dns")


class TestLookupRFC8427(TestCase):
    def setUp(self) -> None:
        self.lookup = lookup_loader.get("community.dns.lookup_rfc8427")

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
                        "target": dns.name.from_unicode("nope.example.com", origin=None),
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
                        "target": dns.name.from_unicode("nope.example.com", origin=None),
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
