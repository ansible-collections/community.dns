# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import MagicMock


def mock_resolver(default_nameservers, nameserver_resolve_sequence):
    def create_resolver(configure=True):
        resolver = MagicMock()
        resolver.nameservers = default_nameservers if configure else []

        def mock_resolver_resolve(target, rdtype=None, lifetime=None):
            resolver_index = tuple(sorted(resolver.nameservers))
            assert resolver_index in nameserver_resolve_sequence, 'No resolver sequence for {0}'.format(resolver_index)
            resolve_sequence = nameserver_resolve_sequence[resolver_index]
            assert len(resolve_sequence) > 0, 'Resolver sequence for {0} is empty'.format(resolver_index)
            resolve_data = resolve_sequence[0]
            del resolve_sequence[0]

            assert target == resolve_data['target'], 'target: {0!r} vs {1!r}'.format(target, resolve_data['target'])
            assert rdtype == resolve_data.get('rdtype'), 'rdtype: {0!r} vs {1!r}'.format(rdtype, resolve_data.get('rdtype'))
            assert lifetime == resolve_data['lifetime'], 'lifetime: {0!r} vs {1!r}'.format(lifetime, resolve_data['lifetime'])

            if 'raise' in resolve_data:
                raise resolve_data['raise']

            return resolve_data['result']

        resolver.resolve = MagicMock(side_effect=mock_resolver_resolve)
        return resolver

    return create_resolver


def mock_query_udp(call_sequence):
    def udp(query, nameserver, **kwargs):
        assert len(call_sequence) > 0, 'UDP query call sequence is empty'
        call = call_sequence[0]
        del call_sequence[0]

        assert query.question[0].name == call['query_target'], 'query_target: {0!r} vs {1!r}'.format(query.question[0].name, call['query_target'])
        assert query.question[0].rdtype == call['query_type'], 'query_type: {0!r} vs {1!r}'.format(query.question[0].rdtype, call['query_type'])
        assert nameserver == call['nameserver'], 'nameserver: {0!r} vs {1!r}'.format(nameserver, call['nameserver'])
        assert kwargs == call['kwargs'], 'kwargs: {0!r} vs {1!r}'.format(kwargs, call['kwargs'])

        if 'raise' in call:
            raise call['raise']

        return call['result']

    return udp


def create_mock_answer(rrset=None):
    answer = MagicMock()
    answer.rrset = rrset
    return answer


def create_mock_response(rcode, authority=None, answer=None):
    response = MagicMock()
    response.rcode = MagicMock(return_value=rcode)
    response.authority = authority or []
    response.answer = answer or []
    return response
