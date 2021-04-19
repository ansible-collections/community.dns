# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import MagicMock, patch

from ansible_collections.community.dns.plugins.module_utils.hosttech.json_api import (
    HostTechJSONAPI,
)


# TODO: test _create_record_from_json and _record_to_json for every single record type!


def test_list_pagination():
    def get_1(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 2
        assert query['limit'] == 1
        assert query['offset'] in [0, 1, 2]
        if query['offset'] < 2:
            return {'data': [query['offset']]}, {}
        else:
            return {'data': []}, {}
    
    def get_2(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content is True
        assert expected == [200]
        assert query is not None
        assert len(query) == 3
        assert query['foo'] == 'bar'
        assert query['limit'] == 2
        assert query['offset'] in [0, 2]
        if query['offset'] < 2:
            return {'data': ['bar', 'baz']}, {}
        else:
            return {'data': ['foo']}, {}

    api = HostTechJSONAPI(MagicMock(), '123')

    api._get = MagicMock(side_effect=get_1)
    result = api._list_pagination('https://example.com', block_size=1)
    assert result == [0, 1]

    api._get = MagicMock(side_effect=get_2)
    result = api._list_pagination('https://example.com', query=dict(foo='bar'), block_size=2)
    assert result == ['bar', 'baz', 'foo']
