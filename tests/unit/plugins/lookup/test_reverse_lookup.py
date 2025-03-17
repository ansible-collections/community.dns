# -*- coding: utf-8 -*-
# Copyright (c) 2025, Felix Fontein <felix@fontein.de>
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


class TestLookup(TestCase):
    def setUp(self) -> None:
        self.lookup = lookup_loader.get("community.dns.reverse_lookup")

    def test_simple(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "4.3.2.1.in-addr.arpa.", origin=None
                        ),
                        "search": False,
                        "rdtype": dns.rdatatype.PTR,
                        "lifetime": 10,
                        "result": create_mock_answer(
                            dns.rrset.from_rdata(
                                "4.3.2.1.in-addr.arpa.",
                                300,
                                dns.rdata.from_text(
                                    dns.rdataclass.IN, dns.rdatatype.PTR, "example.com."
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
                    result = self.lookup.run(["1.2.3.4"])

        print(result)
        assert len(result) == 1
        assert result[0] == "example.com."

    def test_nxdomain(self) -> None:
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "4.3.2.1.in-addr.arpa.", origin=None
                        ),
                        "search": False,
                        "rdtype": dns.rdatatype.PTR,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.NXDOMAIN),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    result = self.lookup.run(["1.2.3.4"])

        print(result)
        assert len(result) == 0

    def test_unexpected_resolver_error(self) -> None:
        fake_query = MagicMock()
        fake_query.question = "Doctor Who?"
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "4.3.2.1.in-addr.arpa.", origin=None
                        ),
                        "search": False,
                        "rdtype": dns.rdatatype.PTR,
                        "lifetime": 10,
                        "result": create_mock_answer(rcode=dns.rcode.REFUSED),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["1.2.3.4"])

        print(exc.value.args[0])
        assert (
            exc.value.args[0]
            == "Unexpected resolving error for 4.3.2.1.in-addr.arpa.: Error REFUSED while querying ['1.1.1.1']"
        )

    def test_unexpected_dns_error(self) -> None:
        fake_query = MagicMock()
        fake_query.question = "Doctor Who?"
        resolver = mock_resolver(
            ["1.1.1.1"],
            {
                ("1.1.1.1",): [
                    {
                        "target": dns.name.from_unicode(
                            "4.3.2.1.in-addr.arpa.", origin=None
                        ),
                        "search": False,
                        "rdtype": dns.rdatatype.PTR,
                        "lifetime": 10,
                        "raise": dns.exception.SyntaxError("foo"),
                    },
                ],
            },
        )
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["1.2.3.4"])

        print(exc.value.args[0])
        assert (
            exc.value.args[0] == "Unexpected DNS error for 4.3.2.1.in-addr.arpa.: foo"
        )

    def test_not_ip(self) -> None:
        resolver = mock_resolver([], {})
        with patch("dns.resolver.get_default_resolver", resolver):
            with patch("dns.resolver.Resolver", resolver):
                with patch("dns.query.udp", mock_query_udp([])):
                    with pytest.raises(AnsibleLookupError) as exc:
                        self.lookup.run(["1.2.3.4.5"])

        print(exc.value.args[0])
        assert exc.value.args[0].startswith("Cannot parse IP address '1.2.3.4.5': ")
