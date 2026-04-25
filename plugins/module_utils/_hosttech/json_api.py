# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

# The API documentation can be found here: https://api.ns1.hosttech.eu/api/documentation/

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._json_api_helper import (
    JSONAPIHelper,
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

if t.TYPE_CHECKING:
    from collections.abc import Sequence  # pragma: no cover

    from .._http import HTTPHelper  # pragma: no cover
    from .._record import IDNSRecord  # pragma: no cover
    from .._zone_record_api import NotProvidedType  # pragma: no cover


def _create_record_from_json(
    source: dict[str, t.Any], record_type: str | None = None
) -> DNSRecord[int]:
    source = dict(source)
    record_type = source.pop("type", record_type)
    if record_type is None:
        raise DNSAPIError("Record from API has no type")

    name: str | None = source.pop("name", None)
    target: str
    if record_type == "A":
        target = source.pop("ipv4")
    elif record_type == "AAAA":
        target = source.pop("ipv6")
    elif record_type == "CAA":
        target = f"{source.pop('flag')} {source.pop('tag')} \"{source.pop('value')}\""
    elif record_type == "CNAME":
        target = source.pop("cname")
    elif record_type == "MX":
        mx_name, name = name, source.pop("ownername")
        target = f"{source.pop('pref')} {mx_name}"
    elif record_type == "NS":
        name = source.pop("ownername")
        target = source.pop("targetname")
    elif record_type == "PTR":
        ptr_name, name = name, ""
        target = f"{source.pop('origin')} {ptr_name}"
    elif record_type == "SRV":
        name = source.pop("service")
        target = f"{source.pop('priority')} {source.pop('weight')} {source.pop('port')} {source.pop('target')}"
    elif record_type in ("TXT", "TLSA"):
        target = source.pop("text")
    else:
        raise DNSAPIError(f"Cannot parse unknown record type: {record_type}")

    result = DNSRecord(
        record_id=source.pop("id"), record_type=record_type, target=target
    )
    ttl = source.pop("ttl")
    result.ttl = int(ttl) if ttl is not None else None
    result.extra["comment"] = source.pop("comment")
    result.prefix = name or None  # API returns '', we want None
    result.extra.update(source)
    return result


def _create_zone_from_json(source: dict[str, t.Any]) -> DNSZone[int]:
    zone = DNSZone(zone_id=source["id"], name=source["name"])
    zone.info = {
        "dnssec": source["dnssec"],
        "dnssec_email": source.get("dnssec_email"),
        "ds_records": source.get("ds_records"),
        "email": source.get("email"),
        "ttl": source["ttl"],
    }
    return zone


def _create_zone_with_records_from_json(
    source: dict[str, t.Any],
    prefix: str | None | NotProvidedType = NOT_PROVIDED,
    record_type: str | NotProvidedType = NOT_PROVIDED,
) -> DNSZoneWithRecords[int, int]:
    return DNSZoneWithRecords(
        _create_zone_from_json(source),
        filter_records(
            [_create_record_from_json(record) for record in source["records"]],
            prefix=prefix,
            record_type=record_type,
        ),
    )


def _record_to_json(
    record: IDNSRecord[int | None], include_id: bool = False, include_type: bool = True
) -> dict[str, t.Any]:
    result: dict[str, t.Any] = {
        "ttl": record.ttl,
        "comment": record.extra.get("comment") or "",
    }
    if include_type:
        result["type"] = record.type
    if include_id:
        result["id"] = record.id

    if record.type == "A":
        result["name"] = record.prefix or ""
        result["ipv4"] = record.target
    elif record.type == "AAAA":
        result["name"] = record.prefix or ""
        result["ipv6"] = record.target
    elif record.type == "CAA":
        result["name"] = record.prefix or ""
        try:
            flag, tag, value = record.target.split(" ", 2)
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            result["flag"] = flag
            result["tag"] = tag
            result["value"] = value
        except Exception as e:
            raise DNSAPIError(
                f'Cannot split {record.type} record "{record.target}" into flag, tag and value: {e}'
            ) from e
    elif record.type == "CNAME":
        result["name"] = record.prefix or ""
        result["cname"] = record.target
    elif record.type == "MX":
        result["ownername"] = record.prefix or ""
        try:
            pref, name = record.target.split(" ", 1)
            result["pref"] = int(pref)
            result["name"] = name
        except Exception as e:
            raise DNSAPIError(
                f'Cannot split {record.type} record "{record.target}" into integer preference and name: {e}'
            ) from e
    elif record.type == "NS":
        result["ownername"] = record.prefix or ""
        result["targetname"] = record.target
    elif record.type == "PTR":
        try:
            origin, name = record.target.split(" ", 1)
            result["origin"] = origin
            result["name"] = name
        except Exception as e:
            raise DNSAPIError(
                f'Cannot split {record.type} record "{record.target}" into origin and name: {e}'
            ) from e
    elif record.type == "SRV":
        result["service"] = record.prefix or ""
        try:
            priority, weight, port, target = record.target.split(" ", 3)
            result["priority"] = int(priority)
            result["weight"] = int(weight)
            result["port"] = int(port)
            result["target"] = target
        except Exception as e:
            raise DNSAPIError(
                f'Cannot split {record.type} record "{record.target}" into integer priority, integer weight, integer port and target: {e}'
            ) from e
    elif record.type in ("TXT", "TLSA"):
        result["name"] = record.prefix or ""
        result["text"] = record.target
    else:
        raise DNSAPIError(f"Cannot serialize unknown record type: {record.type}")

    return result


def _pagination_query(
    query: dict[str, str] | Sequence[tuple[str, str]] | None,
    *,
    block_size: int,
    offset: int,
) -> dict[str, str] | Sequence[tuple[str, str]]:
    if isinstance(query, dict):
        query_map = query.copy()
        query_map["limit"] = str(block_size)
        query_map["offset"] = str(offset)
        return query_map
    query_list = list(query) if query else []
    query_list.append(("limit", str(block_size)))
    query_list.append(("offset", str(offset)))
    return query_list


class HostTechJSONAPI(ZoneRecordAPI[int, int], JSONAPIHelper):
    def __init__(
        self,
        http_helper: HTTPHelper,
        token: str,
        api="https://api.ns1.hosttech.eu/api/",
        debug: bool = False,
    ) -> None:
        """
        Create a new HostTech API instance with given API token.
        """
        JSONAPIHelper.__init__(self, http_helper, token, api=api, debug=debug)

    def _extract_error_message(self, result: t.Any | None) -> str:
        if result is None:
            return ""
        if isinstance(result, dict):
            res = ""
            if result.get("message"):
                res = f"{res} with message \"{result['message']}\""
            if "errors" in result and isinstance(result["errors"], dict):
                for k, v in sorted(result["errors"].items()):
                    if isinstance(v, list):
                        v = "; ".join(v)
                    res = f'{res} (field "{k}": {v})'
            if res:
                return res
        return f" with data: {result}"

    def _create_headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
            "authorization": f"Bearer {self._token}",
        }

    def _list_pagination(
        self,
        url: str,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        block_size: int = 100,
    ) -> list[t.Any]:
        result = []
        offset = 0
        while True:
            query_ = _pagination_query(query, block_size=block_size, offset=offset)
            res, dummy = self._get(
                url,
                query=query_,
                must_have_content=True,
                expected=[200],
                require_json_object=True,
            )
            result.extend(res["data"])
            if len(res["data"]) < block_size:
                return result
            offset += block_size

    def get_zone_with_records_by_id(
        self,
        zone_id: int,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> DNSZoneWithRecords[int, int] | None:
        """
        Given a zone ID, return the zone contents with records if found.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        result, info = self._get(
            f"user/v1/zones/{zone_id}",
            expected=[200, 404],
            must_have_content=[200],
            require_json_object=True,
        )
        if info["status"] == 404 or result is None:
            return None
        return _create_zone_with_records_from_json(
            result["data"], prefix=prefix, record_type=record_type
        )

    def get_zone_with_records_by_name(
        self,
        name: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> DNSZoneWithRecords[int, int] | None:
        """
        Given a zone name, return the zone contents with records if found.

        @param name: The zone name (string)
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return The zone information with records (DNSZoneWithRecords), or None if not found
        """
        result = self._list_pagination("user/v1/zones", query={"query": name})
        for zone in result:
            if zone["name"] == name:
                zone_result, dummy = self._get(
                    f"user/v1/zones/{zone['id']}",
                    expected=[200],
                    require_json_object=True,
                )
                return _create_zone_with_records_from_json(
                    zone_result["data"], prefix=prefix, record_type=record_type
                )
        return None

    def get_zone_records(
        self,
        zone_id: int,
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
        if record_type is not NOT_PROVIDED:
            query["type"] = record_type.upper()  # type: ignore  # Is a string
        result, info = self._get(
            f"user/v1/zones/{zone_id}/records",
            query=query,
            expected=[200, 404],
            must_have_content=[200],
            require_json_object=True,
        )
        if info["status"] == 404 or result is None:
            return None
        return filter_records(
            [_create_record_from_json(record) for record in result["data"]],
            prefix=prefix,
            record_type=record_type,
        )

    def get_zone_by_name(self, name: str) -> DNSZone[int] | None:
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        result = self._list_pagination("user/v1/zones", query={"query": name})
        for zone in result:
            if zone["name"] == name:
                # We cannot simply return `_create_zone_from_json(zone)`, since this contains less information!
                return self.get_zone_by_id(zone["id"])
        return None

    def get_zone_by_id(self, zone_id: int) -> DNSZone[int] | None:
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get(
            f"user/v1/zones/{zone_id}",
            expected=[200, 404],
            must_have_content=[200],
            require_json_object=True,
        )
        if info["status"] == 404 or result is None:
            return None
        return _create_zone_from_json(result["data"])

    def add_record(
        self, zone_id: int, record: IDNSRecord[int | None]
    ) -> DNSRecord[int]:
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = _record_to_json(record, include_id=False, include_type=True)
        result, dummy = self._post(
            f"user/v1/zones/{zone_id}/records",
            data=data,
            expected=[201],
            require_json_object=True,
        )
        return _create_record_from_json(result["data"])

    def update_record(self, zone_id: int, record: DNSRecord[int]) -> DNSRecord[int]:
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to update record!")
        data = _record_to_json(record, include_id=False, include_type=False)
        result, dummy = self._put(
            f"user/v1/zones/{zone_id}/records/{record.id}",
            data=data,
            expected=[200],
            require_json_object=True,
        )
        return _create_record_from_json(result["data"])

    def delete_record(self, zone_id: int, record: DNSRecord[int]) -> bool:
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to delete record!")
        dummy, info = self._delete(
            f"user/v1/zones/{zone_id}/records/{record.id}",
            must_have_content=False,
            expected=[204, 404],
            require_json_object=True,
        )
        return info["status"] == 204
