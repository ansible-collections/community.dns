# Copyright (c) 2026, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest
from ansible_collections.community.internal_test_tools.tests.unit.compat.mock import (
    MagicMock,
)

from ansible_collections.community.dns.plugins.module_utils._infomaniak.api import (
    InfomaniakJSONAPI,
    q,
)
from ansible_collections.community.dns.plugins.module_utils._record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    DNSAPIError,
)


def test_list_pagination():
    def get_1(
        url,
        query=None,
        must_have_content=True,
        expected=None,
        require_json_object=False,
    ):
        assert url == "https://example.com"
        assert must_have_content is True
        assert expected == [200]
        assert require_json_object is True
        assert query is not None
        assert len(query) == 2
        assert query[0] == ("per_page", "1")
        assert query[1] in [("page", "1"), ("page", "2"), ("page", "3")]
        page = int(query[1][1])
        if page < 3:
            return {
                "data": [page],
                "page": page,
                "per_page": 1,
                "last_page": 3,
                "total_entries": 2,
            }, {"status": 200}
        return {
            "data": [],
            "page": page,
            "per_page": 1,
            "last_page": 3,
            "total_entries": 2,
        }, {"status": 200}

    def get_2(
        url,
        query=None,
        must_have_content=True,
        expected=None,
        require_json_object=False,
    ):
        assert url == "https://example.com"
        assert must_have_content is True
        assert require_json_object is True
        assert query is not None
        assert len(query) == 3
        assert query["foo"] == "bar"
        assert query["per_page"] == "2"
        assert query["page"] in ["1", "2"]
        page = int(query["page"])
        assert expected == ([200, 404] if page == 1 else [200])
        if page < 2:
            return {
                "data": ["bar", "baz"],
                "page": page,
                "per_page": 2,
                "last_page": 2,
                "total_entries": 3,
            }, {"status": 200}
        return {
            "data": ["foo"],
            "page": page,
            "per_page": 2,
            "last_page": 2,
            "total_entries": 3,
        }, {"status": 200}

    def get_3(
        url,
        query=None,
        must_have_content=True,
        expected=None,
        require_json_object=False,
    ):
        assert url == "https://example.com"
        assert must_have_content is True
        assert expected == [200, 404]
        assert require_json_object is True
        assert query is not None
        assert len(query) == 2
        assert query[0] == ("per_page", "100")
        assert query[1] == ("page", "1")
        return None, {"status": 404}

    api = InfomaniakJSONAPI(http_helper=MagicMock(), token="123")

    api._get = MagicMock(side_effect=get_1)
    result = api._list_pagination("https://example.com", per_page=1, accept_404=False)
    assert result == [1, 2]

    api._get = MagicMock(side_effect=get_2)
    result = api._list_pagination(
        "https://example.com",
        query={"foo": "bar"},
        per_page=2,
        accept_404=True,
    )
    assert result == ["bar", "baz", "foo"]

    api._get = MagicMock(side_effect=get_3)
    result = api._list_pagination("https://example.com", accept_404=True)
    assert result is None


def test_update_id_missing():
    api = InfomaniakJSONAPI(http_helper=MagicMock(), token="123")
    with pytest.raises(DNSAPIError) as exc:
        api.update_record(1, DNSRecord(record_id=None, record_type="TXT", target=""))
    assert exc.value.args[0] == "Need record ID to update record!"


def test_update_id_delete():
    api = InfomaniakJSONAPI(http_helper=MagicMock(), token="123")
    with pytest.raises(DNSAPIError) as exc:
        api.delete_record(1, DNSRecord(record_id=None, record_type="TXT", target=""))
    assert exc.value.args[0] == "Need record ID to delete record!"


def test_extract_error_message():
    api = InfomaniakJSONAPI(http_helper=MagicMock(), token="123")
    assert api._extract_error_message(None) == ""
    assert api._extract_error_message("foo") == " with data: foo"
    assert api._extract_error_message({}) == " with data: {}"
    assert api._extract_error_message({"message": ""}) == " with data: {'message': ''}"
    assert api._extract_error_message({"error": 42}) == " with data: {'error': 42}"
    assert api._extract_error_message({"error": {}}) == " with data: {'error': {}}"
    assert (
        api._extract_error_message({"error": {"description": "foo"}})
        == " with data: {'error': {'description': 'foo'}}"
    )
    assert (
        api._extract_error_message({"error": {"description": "foo", "code": "bar"}})
        == "[bar] foo"
    )


def test_q():
    assert q(None) == ""
    assert q("") == ""
    assert q(0) == "0"
    assert q(42) == "42"
    assert q(" ") == "%20"
