# Copyright (c) 2026 Felix Fontein
# Copyright (c) 2026 Plexim GmbH
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

# API docs:
# https://developer.infomaniak.com/docs/api/get/2/zones/%7Bzone%7D/records

# **NOTE** that we're using the zone's FQDN as the zone ID, instead of the integer
# value provided in the zone object, since Infomaniak's API does not allow to
# access zone or record data with the integer ID, only with the FQDN.

from __future__ import annotations

import typing as t
from urllib.parse import quote

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec
from ansible_collections.community.dns.plugins.module_utils._json_api_helper import (
    JSONAPIHelper,
)
from ansible_collections.community.dns.plugins.module_utils._provider import (
    ProviderInformation,
)
from ansible_collections.community.dns.plugins.module_utils._record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils._zone import (
    DNSZone,
    DNSZoneWithRecords,
)
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    NOT_PROVIDED,
    DNSAPIError,
    ZoneRecordAPI,
    filter_records,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from .._argspec import OptionProvider
    from .._http import HTTPHelper
    from .._provider import AnsibleType
    from .._record import IDNSRecord
    from .._zone_record_api import NotProvidedType


def _create_record_from_json(source: dict[str, t.Any]) -> DNSRecord[int]:
    record_type = source.get("type")
    if record_type is None:  # pragma: no cover
        raise DNSAPIError("Record from API has no type")
    prefix: str | None = source["source"]
    if prefix in ("", "."):
        prefix = None
    result = DNSRecord(
        record_id=source["id"],
        record_type=record_type,
        target=source["target"],
    )
    result.ttl = source["ttl"]
    result.prefix = prefix
    return result


def _create_zone_from_json(source: dict[str, t.Any]) -> DNSZone[str]:
    # We don't use the "id" field.
    zone = DNSZone(zone_id=source["fqdn"], name=source["fqdn"])
    zone.info = {
        "dnssec": source["dnssec"],  # dict with key "is_enabled"
        "id": source["id"],  # integer
        "nameservers": source["nameservers"],  # list of strings
    }
    return zone


def _create_zone_with_records_from_json(
    source: dict[str, t.Any],
    prefix: str | None | NotProvidedType = NOT_PROVIDED,
    record_type: str | NotProvidedType = NOT_PROVIDED,
) -> DNSZoneWithRecords[str, int]:
    return DNSZoneWithRecords(
        _create_zone_from_json(source),
        filter_records(
            [_create_record_from_json(record) for record in source["records"]],
            prefix=prefix,
            record_type=record_type,
        ),
    )


def _pagination_query(
    query: dict[str, str] | Sequence[tuple[str, str]] | None,
    *,
    per_page: int,
    page: int,
) -> dict[str, str] | Sequence[tuple[str, str]]:
    if isinstance(query, dict):
        query_map = query.copy()
        query_map["per_page"] = str(per_page)
        query_map["page"] = str(page)
        return query_map
    query_list = list(query) if query else []
    query_list.append(("per_page", str(per_page)))
    query_list.append(("page", str(page)))
    return query_list


def q(value: str | int | None) -> str:
    if value is None:
        return ""
    return quote(str(value), safe="", encoding="utf-8", errors=None)


class InfomaniakJSONAPI(ZoneRecordAPI[str, int], JSONAPIHelper):
    def __init__(
        self,
        *,
        http_helper: HTTPHelper,
        token: str,
        api: str = "https://api.infomaniak.com",
        debug: bool = False,
    ) -> None:
        """
        Create a new Infomaniak API instance with given API token.
        """
        JSONAPIHelper.__init__(self, http_helper, token, api=api, debug=debug)

    def _extract_error_message(self, result: t.Any | None) -> str:
        if result is None:
            return ""
        if isinstance(result, dict):
            res = ""
            if "error" in result:
                error = result["error"]
                if (
                    isinstance(error, dict)
                    and isinstance(error.get("code"), str)
                    and isinstance(error.get("description"), str)
                ):
                    res = f"[{error['code']}] {error['description']}"
            if res:
                return res
        return f" with data: {result}"

    def _create_headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self._token}",
        }

    @t.overload
    def _list_pagination(
        self,
        url: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        per_page: int = 100,
        allow_404: t.Literal[False] = False,
    ) -> list[t.Any]: ...

    @t.overload
    def _list_pagination(
        self,
        url: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        per_page: int = 100,
        allow_404: t.Literal[True],
    ) -> list[t.Any] | None: ...

    def _list_pagination(
        self,
        url: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        per_page: int = 100,
        allow_404: bool = False,
    ) -> list[t.Any] | None:
        result = []
        page = 1
        while True:
            query_ = _pagination_query(query, per_page=per_page, page=page)
            res, info = self._get(
                url,
                query=query_,
                must_have_content=True,
                expected=[200, 404] if allow_404 and page == 1 else [200],
                require_json_object=True,
            )
            if info["status"] == 404:
                return None
            result.extend(res["data"])
            if len(res["data"]) < per_page:
                return result
            page += 1

    def get_zone_with_records_by_id(
        self,
        zone_id: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> DNSZoneWithRecords[str, int] | None:
        """
        Given a zone ID, return the zone contents with records if found.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        return self.get_zone_with_records_by_name(
            zone_id, prefix=prefix, record_type=record_type
        )  # pragma: no cover

    def get_zone_with_records_by_name(
        self,
        name: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> DNSZoneWithRecords[str, int] | None:
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        result, info = self._get(
            f"/2/zones/{q(name)}?with=records",
            expected=[200, 404],
            must_have_content=[200, 404],
            require_json_object=True,
        )
        if info["status"] == 404 or result is None:
            return None
        return _create_zone_with_records_from_json(
            result["data"], prefix=prefix, record_type=record_type
        )

    def get_zone_records(
        self,
        zone_id: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> list[DNSRecord[int]] | None:
        """
        Given a zone ID, return a list of records, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecord objects, or None if zone was not found
        """
        query: dict[str, str] = {}
        if prefix is not NOT_PROVIDED:
            query["filter[source]"] = prefix or "."  # type: ignore  # Is a string
        if record_type is not NOT_PROVIDED:
            query["filter[types][]"] = record_type.upper()  # type: ignore  # Is a string
        result = self._list_pagination(
            f"/2/zones/{q(zone_id)}/records",
            query=query,
            allow_404=True,
        )
        if result is None:
            return None
        return filter_records(
            [_create_record_from_json(record) for record in result],
            prefix=prefix,
            record_type=record_type,
        )

    def get_zone_by_name(self, name: str) -> DNSZone[str] | None:
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get(
            f"/2/zones/{q(name)}",
            expected=[200, 404],
            must_have_content=[200, 404],
            require_json_object=True,
        )
        if info["status"] == 404 or result is None:
            return None
        return _create_zone_from_json(result["data"])

    def get_zone_by_id(self, zone_id: str) -> DNSZone[str] | None:
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        return self.get_zone_by_name(zone_id)  # pragma: no cover

    def add_record(
        self, zone_id: str, record: IDNSRecord[int | None]
    ) -> DNSRecord[int]:
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = {
            "type": record.type,
            "ttl": record.ttl,
            "source": record.prefix or ".",
            "target": record.target,
        }
        result, dummy = self._post(
            f"/2/zones/{q(zone_id)}/records",
            data=data,
            # Documentation says 200, API actually returns 201...
            expected=[200, 201],
            require_json_object=True,
        )
        return _create_record_from_json(result["data"])

    def update_record(self, zone_id: str, record: DNSRecord[int]) -> DNSRecord[int]:
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to update record!")
        data = {
            "ttl": record.ttl,
            "target": record.target,
        }
        result, dummy = self._put(
            f"/2/zones/{q(zone_id)}/records/{q(record.id)}",
            data=data,
            expected=[200],
            require_json_object=True,
        )
        return _create_record_from_json(result["data"])

    def delete_record(self, zone_id: str, record: DNSRecord[int]) -> bool:
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to delete record!")
        result, info = self._delete(
            f"/2/zones/{q(zone_id)}/records/{q(record.id)}",
            expected=[200, 404],
            require_json_object=True,
        )
        return info["status"] == 200 and result["result"] == "success"


class InfomaniakProviderInformation(ProviderInformation):
    def get_supported_record_types(self) -> list[str]:
        """
        Return a list of supported record types.
        """
        return [
            "A",
            "AAAA",
            "CAA",
            "CNAME",
            "DNAME",
            "DNSKEY",
            "DS",
            "MX",
            "NS",
            "PTR",
            "SMIMEA",
            "SOA",
            "SRV",
            "SSHFP",
            "TLSA",
            "TXT",
        ]

    def get_zone_id_type(self) -> AnsibleType:
        """
        Return the (short) type for zone IDs, like ``'int'`` or ``'str'``.
        """
        return "str"

    def is_zone_id_equal_to_zone_name(self) -> bool:
        """
        Whether the zone ID is equal to the zone's name (FQDN).

        If ``True``, implies that ``get_zone_id_type()`` returns ``str``.
        """
        return True

    def get_record_id_type(self) -> AnsibleType:
        """
        Return the (short) type for record IDs, like ``'int'`` or ``'str'``.
        """
        return "int"  # pragma: no cover

    def get_record_default_ttl(self) -> int | None:
        """
        Return the default TTL for records, like 300, 3600 or None.
        None means that some other TTL (usually from the zone) will be used.
        """
        # There is no default, every record must have a TTL, so we just pick a "random" number.
        return 300

    def normalize_prefix(self, prefix: str | None) -> str | None:
        """
        Given a prefix (string or None), return its normalized form.

        The result should always be None for the trivial prefix, and a non-zero length DNS name
        for a non-trivial prefix.

        If a provider supports other identifiers for the trivial prefix, such as '@', this
        function needs to convert them to None as well.
        """
        return None if prefix in (".", "") else prefix

    def txt_record_handling(
        self,
    ) -> t.Literal["decoded", "encoded", "encoded-no-char-encoding"]:
        """
        Return how the API handles TXT records.

        Returns one of the following strings:
        * 'decoded' - the API works with unencoded values
        * 'encoded' - the API works with encoded values
        * 'encoded-no-char-encoding' - the API works with encoded values, but without character encoding
        """
        return "encoded-no-char-encoding"

    def txt_decode_lenient_from_api(self) -> bool:
        """
        Whether TXT records send from the API should be decoded with lenient=True.
        """
        return True


def create_infomaniak_provider_information(
    option_provider: OptionProvider | None = None,
) -> InfomaniakProviderInformation:
    return InfomaniakProviderInformation()


def create_infomaniak_argument_spec() -> ArgumentSpec:
    return ArgumentSpec(
        argument_spec={
            "infomaniak_token": {
                "type": "str",
                "required": True,
                "no_log": True,
                "aliases": ["api_token"],
            },
        },
    )


def create_infomaniak_api(
    option_provider: OptionProvider, http_helper: HTTPHelper
) -> InfomaniakJSONAPI:
    token = option_provider.get_option("infomaniak_token")
    if token is not None:
        return InfomaniakJSONAPI(http_helper=http_helper, token=token)

    raise DNSAPIError("infomaniak_token must be provided!")  # pragma: no cover
