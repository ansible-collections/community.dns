# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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
        assert must_have_content == [200]
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
            }, {'status': 200}
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
            }, {'status': 200}

    def get_2(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content == [200]
        assert expected == ([200, 404] if query['page'] == 1 else [200])
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
            }, {'status': 200}
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
            }, {'status': 200}

    def get_3(url, query=None, must_have_content=True, expected=None):
        assert url == 'https://example.com'
        assert must_have_content == [200]
        assert expected == [200, 404]
        assert query is not None
        assert len(query) == 2
        assert query['per_page'] == 100
        assert query['page'] == 1
        return None, {'status': 404}

    api = HetznerAPI(MagicMock(), '123')

    api._get = MagicMock(side_effect=get_1)
    result = api._list_pagination('https://example.com', 'data', block_size=1, accept_404=False)
    assert result == [1, 2]

    api._get = MagicMock(side_effect=get_2)
    result = api._list_pagination('https://example.com', 'foobar', query=dict(foo='bar'), block_size=2, accept_404=True)
    assert result == ['bar', 'baz', 'foo']

    api._get = MagicMock(side_effect=get_3)
    result = api._list_pagination('https://example.com', 'baz', accept_404=True)
    assert result is None


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


def test_extract_error_message():
    api = HetznerAPI(MagicMock(), '123')
    assert api._extract_error_message(None) == ''
    assert api._extract_error_message('foo') == ' with data: foo'
    assert api._extract_error_message(dict()) == ' with data: {}'
    assert api._extract_error_message(dict(message='')) == " with data: {'message': ''}"
    assert api._extract_error_message(dict(message='foo')) == ' with message "foo"'
    assert api._extract_error_message(dict(message='foo', error='')) == ' with message "foo"'
    assert api._extract_error_message(dict(message='foo', error=dict())) == ' with message "foo"'
    assert api._extract_error_message(dict(message='foo', error=dict(code=123))) == ' (error code 123) with message "foo"'
    assert api._extract_error_message(dict(message='foo', error=dict(message='baz'))) == ' with error message "baz" with message "foo"'
    assert api._extract_error_message(dict(message='foo', error=dict(message='baz', code=123))) == (
        ' with error message "baz" (error code 123) with message "foo"'
    )
    assert api._extract_error_message(dict(error=dict(message='baz', code=123))) == ' with error message "baz" (error code 123)'
