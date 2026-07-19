# Copyright (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import typing as t

INFOMANIAK_ZONE_JSON = {
    "result": "success",
    "data": {
        "id": 42,
        "fqdn": "example.com",
        "dnssec": {
            "is_enabled": True,
        },
        "nameservers": [
            "ns1.infomaniak.ch",
            "ns2.infomaniak.ch",
        ],
    },
}

INFOMANIAK_JSON_DEFAULT_ENTRIES = [
    {
        "id": 1,
        "type": "A",
        "source": ".",
        "target": "1.2.3.4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 2,
        "type": "A",
        "source": "*",
        "target": "1.2.3.5",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 3,
        "type": "AAAA",
        "source": ".",
        "target": "2001:1:2::3",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 4,
        "type": "AAAA",
        "source": "*",
        "target": "2001:1:2::4",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 5,
        "type": "MX",
        "source": ".",
        "target": "10 example.com",
        "ttl": 3600,
        "updated_at": 12345678,
    },
    {
        "id": 6,
        "type": "NS",
        "source": ".",
        "target": "ns1.infomaniak.ch",
        "ttl": 86400,
        "updated_at": 12345678,
    },
    {
        "id": 7,
        "type": "NS",
        "source": ".",
        "target": "ns2.infomaniak.ch",
        "ttl": 86400,
        "updated_at": 12345678,
    },
    {
        "id": 8,
        "type": "SOA",
        "source": ".",
        "target": "ns1.infomaniak.ch. hostmaster.infomaniak.ch. 2021070900 86400 10800 3600000 3600",
        "ttl": 86400,
        "updated_at": 12345678,
    },
    {
        "id": 9,
        "type": "TXT",
        "source": "foo",
        "target": '"bär" " \\"with quotes\\"" " " "(use \\\\ to escape)"',
        "ttl": 86400,
        "updated_at": 12345678,
    },
]


def get_infomaniak_json_pagination_meta(
    total_entries: int, page: int = 1, per_page: int = 100, last_page: int = 1
) -> dict[str, t.Any]:
    return {
        "page": page,
        "pages": last_page,
        "items_per_page": per_page,
        "total": total_entries,
    }


def get_infomaniak_json_records(
    source: str | None = None,
    record_type: str | None = None,
) -> dict[str, t.Any]:
    records = list(INFOMANIAK_JSON_DEFAULT_ENTRIES)
    if record_type is not None:
        records = [record for record in records if record["type"] == record_type]
    if source is not None:
        records = [record for record in records if record["source"] == source]
    return {
        "result": "success",
        "data": records,
        **get_infomaniak_json_pagination_meta(len(records)),
    }


def with_records(
    zone: dict[str, t.Any], records: list[dict[str, t.Any]]
) -> dict[str, t.Any]:
    result = zone.copy()
    zone_data: dict[str, t.Any] = result["data"].copy()
    result["data"] = zone_data
    zone_data["records"] = records
    return result
