# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
)

try:
    import dns.rcode
except ImportError:  # pragma: no cover
    pass  # pragma: no cover


def mock_resolver(default_nameservers, nameserver_resolve_sequence):
    def create_resolver(configure=True):
        resolver = MagicMock()
        resolver.nameservers = default_nameservers if configure else []

        def mock_resolver_resolve(target, rdtype=None, lifetime=None, search=None):
            resolver_index = tuple(sorted(resolver.nameservers))
            assert (
                resolver_index in nameserver_resolve_sequence
            ), f"No resolver sequence for {resolver_index}"
            resolve_sequence = nameserver_resolve_sequence[resolver_index]
            assert (
                len(resolve_sequence) > 0
            ), f"Resolver sequence for {resolver_index} is empty"
            resolve_data = resolve_sequence[0]
            del resolve_sequence[0]

            assert (
                target == resolve_data["target"]
            ), f"target: {target!r} vs {resolve_data['target']!r}"
            assert rdtype == resolve_data.get(
                "rdtype"
            ), f"rdtype: {rdtype!r} vs {resolve_data.get('rdtype')!r}"
            assert (
                lifetime == resolve_data["lifetime"]
            ), f"lifetime: {lifetime!r} vs {resolve_data['lifetime']!r}"
            assert search == resolve_data.get(
                "search"
            ), f"search: {search!r} vs {resolve_data.get('search')!r}"

            if "raise" in resolve_data:
                raise resolve_data["raise"]

            return resolve_data["result"]

        resolver.resolve = MagicMock(side_effect=mock_resolver_resolve)
        return resolver

    return create_resolver


def mock_query_udp(call_sequence):
    def udp(query, nameserver, **kwargs):
        assert len(call_sequence) > 0, "UDP query call sequence is empty"
        call = call_sequence[0]
        del call_sequence[0]

        assert (
            query.question[0].name == call["query_target"]
        ), f"query_target: {query.question[0].name!r} vs {call['query_target']!r}"
        assert (
            query.question[0].rdtype == call["query_type"]
        ), f"query_type: {query.question[0].rdtype!r} vs {call['query_type']!r}"
        assert (
            nameserver == call["nameserver"]
        ), f"nameserver: {nameserver!r} vs {call['nameserver']!r}"
        assert kwargs == call["kwargs"], f"kwargs: {kwargs!r} vs {call['kwargs']!r}"

        if "raise" in call:
            raise call["raise"]

        return call["result"]

    return udp


def create_mock_response(rcode, authority=None, answer=None):
    response = MagicMock()
    response.rcode = MagicMock(return_value=rcode)
    response.authority = authority or []
    response.answer = answer or []
    return response


def create_mock_answer(rrset=None, rcode=None):
    answer = MagicMock()
    answer.response = create_mock_response(
        dns.rcode.NOERROR if rcode is None else rcode, answer=[rrset] if rrset else None
    )
    answer.rrset = rrset
    return answer
