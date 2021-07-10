# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import json

import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import MagicMock, patch

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
)

from ansible_collections.community.dns.plugins.module_utils.hetzner.api import (
    _create_record_from_json,
    _record_to_json,
    HetznerAPI,
)


def test_list_pagination():
    def get_1(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 2
        assert query['per_page'] == 1
        assert query['page'] in [1, 2, 3]
        if query['page'] < 3:
            return {
                'data': [query['page']],
                'meta': {
                    'pagination': {
                        'page': query['page'],
                        'per_page': 1,
                        'last_page': 3,
                        'total_entries': 2,
                    },
                },
            }, {}
        else:
            return {
                'data': [],
                'meta': {
                    'pagination': {
                        'page': query['page'],
                        'per_page': 1,
                        'last_page': 3,
                        'total_entries': 2,
                    },
                },
            }, {}

    def get_2(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 3
        assert query['foo'] == 'bar'
        assert query['per_page'] == 2
        assert query['page'] in [1, 2]
        if query['page'] < 2:
            return {
                'foobar': ['bar', 'baz'],
                'meta': {
                    'pagination': {
                        'page': query['page'],
                        'per_page': 2,
                        'last_page': 2,
                        'total_entries': 3,
                    },
                },
            }, {}
        else:
            return {
                'foobar': ['foo'],
                'meta': {
                    'pagination': {
                        'page': query['page'],
                        'per_page': 2,
                        'last_page': 2,
                        'total_entries': 3,
                    },
                },
            }, {}

    api = HetznerAPI(MagicMock(), '123')

    api._get = MagicMock(side_effect=get_1)
    result = api._list_pagination('https://example.com', 'data', block_size=1)
    assert result == [1, 2]

    api._get = MagicMock(side_effect=get_2)
    result = api._list_pagination('https://example.com', 'foobar', query=dict(foo='bar'), block_size=2)
    assert result == ['bar', 'baz', 'foo']


def test_update_id_missing():
    api = HetznerAPI(MagicMock(), '123')
    with pytest.raises(DNSAPIError) as exc:
        api.update_record(1, DNSRecord())
    assert exc.value.args[0] == 'Need record ID to update record!'


def test_update_id_delete():
    api = HetznerAPI(MagicMock(), '123')
    with pytest.raises(DNSAPIError) as exc:
        api.delete_record(1, DNSRecord())
    assert exc.value.args[0] == 'Need record ID to delete record!'
