# (c) 2021 Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


HETZNER_DEFAULT_ZONE = {
    "id": "42",
    "created": "2021-07-09T11:18:37Z",
    "modified": "2021-07-09T11:18:37Z",
    "legacy_dns_host": "string",
    "legacy_ns": ["string"],
    "name": "example.com",
    "ns": ["string"],
    "owner": "Example",
    "paused": True,
    "permission": "string",
    "project": "string",
    "registrar": "string",
    "status": "verified",
    "ttl": 10800,
    "verified": "2021-07-09T11:18:37Z",
    "records_count": 0,
    "is_secondary_dns": True,
    "txt_verification": {
        "name": "string",
        "token": "string"
    },
}

HETZNER_JSON_ZONE_LIST_RESULT = {
    "zones": [
        HETZNER_DEFAULT_ZONE,
    ],
}

HETZNER_JSON_ZONE_GET_RESULT = {
    "zone": HETZNER_DEFAULT_ZONE,
}

# HETZNER_JSON_ZONE_RECORDS_GET_RESULT = {
#     "data": HETZNER_JSON_DEFAULT_ENTRIES,
# }
