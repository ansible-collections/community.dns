# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

# https://dns.hetzner.com/api-docs

from __future__ import annotations

import json
import time
import typing as t
from collections.abc import Mapping
from urllib.parse import quote

from ansible.module_utils.basic import env_fallback

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec
from ansible_collections.community.dns.plugins.module_utils._json_api_helper import (
    ERROR_CODES,
    UNKNOWN_ERROR,
    JSONAPIHelper,
)
from ansible_collections.community.dns.plugins.module_utils._provider import (
    ProviderInformation,
)
from ansible_collections.community.dns.plugins.module_utils._record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils._record_set import (
    DNSRecordSet,
)
from ansible_collections.community.dns.plugins.module_utils._zone import DNSZone
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    NOT_PROVIDED,
    DNSAPIError,
    ZoneRecordAPI,
    filter_records,
)
from ansible_collections.community.dns.plugins.module_utils._zone_record_set_api import (
    ZoneRecordSetAPI,
    filter_record_sets,
)

if t.TYPE_CHECKING:
    from collections.abc import Collection, Sequence  # pragma: no cover

    from .._argspec import OptionProvider  # pragma: no cover
    from .._http import HTTPHelper, HTTPMethod  # pragma: no cover
    from .._provider import AnsibleType  # pragma: no cover
    from .._record import IDNSRecord  # pragma: no cover
    from .._record_set import IDNSRecordSet  # pragma: no cover
    from .._zone_record_api import NotProvidedType  # pragma: no cover


def _create_zone_from_json(source: dict[str, t.Any]) -> DNSZone[str]:
    info = source.copy()
    zone = DNSZone(zone_id=info.pop("id"), name=info.pop("name"))
    if "legacy_ns" in info:
        info["legacy_ns"] = sorted(info["legacy_ns"])
    zone.info = info
    return zone


@t.overload
def _create_record_from_json(
    source: t.Any, *, record_type: str | None = None, has_id: t.Literal[True] = True
) -> DNSRecord[str]: ...


@t.overload
def _create_record_from_json(
    source: t.Any, *, record_type: str | None = None, has_id: t.Literal[False]
) -> DNSRecord[str | None]: ...


def _create_record_from_json(
    source: t.Any, *, record_type: str | None = None, has_id: bool = True
) -> DNSRecord:
    if not isinstance(source, dict):
        raise DNSAPIError(
            f"Unexpected data {source!r} when expecting DNS record as JSON object"
        )
    source = dict(source)
    result = DNSRecord(
        record_id=source.pop("id") if has_id else None,
        record_type=source.pop("type", record_type),
        target=source.pop("value"),
    )
    result.ttl = source.pop("ttl", None)
    name = source.pop("name", None)
    if name == "@":
        name = None
    result.prefix = name
    source.pop("zone_id", None)
    result.extra.update(source)
    return result


def _record_to_json(record: IDNSRecord[str | None], zone_id: str) -> dict[str, t.Any]:
    result: dict[str, t.Any] = {
        "name": record.prefix or "@",
        "value": record.target,
        "type": record.type,
        "zone_id": zone_id,
    }
    if record.ttl is not None:
        result["ttl"] = record.ttl
    return result


def _pagination_query(
    query: dict[str, str] | Sequence[tuple[str, str]] | None,
    *,
    block_size: int,
    page: int,
) -> dict[str, str] | Sequence[tuple[str, str]]:
    if isinstance(query, dict):
        query_map = query.copy()
        query_map["per_page"] = str(block_size)
        query_map["page"] = str(page)
        return query_map
    query_list = list(query) if query else []
    query_list.append(("per_page", str(block_size)))
    query_list.append(("page", str(page)))
    return query_list


class HetznerAPI(ZoneRecordAPI[str, str], JSONAPIHelper):
    def __init__(
        self, http_helper, token, api="https://dns.hetzner.com/api/", debug=False
    ):
        JSONAPIHelper.__init__(self, http_helper, token, api=api, debug=debug)

    def _create_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Auth-API-Token": self._token,
        }

    def _extract_only_error_message(self, result: t.Any) -> str:
        # These errors are not documented, but are what I experienced the API seems to return:
        if not isinstance(result, dict):
            return f"Unexpected content: {result!r}"
        res = ""
        if isinstance(result.get("error"), dict):
            if "message" in result["error"]:
                msg = result["error"]["message"]
                res = f'{res} with error message "{msg}"'
            if "code" in result["error"]:
                code = result["error"]["code"]
                res = f"{res} (error code {code})"
        if result.get("message"):
            msg = result["message"]
            res = f'{res} with message "{msg}"'
        return res

    def _extract_error_message(self, result: t.Any | None) -> str:
        if result is None:
            return ""
        if isinstance(result, dict):
            res = self._extract_only_error_message(result)
            if res:
                return res
        return f" with data: {result}"

    def _validate(
        self,
        *,
        result: t.Any | None = None,
        info: dict[str, str],
        expected: Collection[int] | None = None,
        method: HTTPMethod = "GET",
    ) -> None:
        super()._validate(result=result, info=info, expected=expected, method=method)
        if isinstance(result, dict):
            error = result.get("error")
            if isinstance(error, dict):
                status = error.get("code")
                if status is None:
                    return
                url = info.get("url")  # not present when using open_url
                if expected is not None and status in expected:
                    return
                error_code = ERROR_CODES.get(status, UNKNOWN_ERROR)
                more = self._extract_error_message(result)
                raise DNSAPIError(
                    f"{method} {url} resulted in API error {status} ({error_code}){more}"
                )

    def _list_pagination(
        self,
        url: str,
        data_key: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        block_size: int = 100,
        accept_404: bool = False,
    ) -> list[t.Any] | None:
        result: list[t.Any] = []
        page = 1
        while True:
            query_ = _pagination_query(query, block_size=block_size, page=page)
            res, info = self._get(
                url,
                query=query_,
                must_have_content=[200],
                expected=[200, 404] if accept_404 and page == 1 else [200],
                require_json_object=True,
            )
            if accept_404 and page == 1 and info["status"] == 404:
                return None
            if not isinstance(res, Mapping):
                raise DNSAPIError(
                    f"GET {url} with query parameters {query_} did not result in JSON object, but {type(res)}"
                )
            result.extend(res[data_key])
            if not isinstance(res.get("meta"), dict) and page == 1:
                return result
            if page >= res["meta"]["pagination"]["last_page"]:
                return result
            page += 1

    def get_zone_by_name(self, name: str) -> DNSZone[str] | None:
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        result, dummy = self._get("v1/zones", expected=[200, 404], query={"name": name})
        if not isinstance(result, Mapping):
            raise DNSAPIError(
                f"Retrieving zone by name resulted in {type(result)} instead of object"
            )
        for zone in result["zones"]:
            if zone.get("name") == name:
                return _create_zone_from_json(zone)
        return None

    def get_zone_by_id(self, zone_id: str) -> DNSZone[str] | None:
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        result, info = self._get(
            f"v1/zones/{zone_id}",
            expected=[200, 404],
            must_have_content=[200],
        )
        if not isinstance(result, Mapping):
            raise DNSAPIError(
                f"Retrieving zone by name resulted in {type(result)} instead of object"
            )
        if info["status"] == 404:
            return None
        return _create_zone_from_json(result["zone"])

    def get_zone_records(
        self,
        zone_id: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> list[DNSRecord[str]] | None:
        """
        Given a zone ID, return a list of records, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecord objects, or None if zone was not found
        """
        result = self._list_pagination(
            "v1/records",
            data_key="records",
            query={"zone_id": zone_id},
            accept_404=True,
        )
        if result is None:
            return None
        return filter_records(
            [_create_record_from_json(record) for record in result],
            prefix=prefix,
            record_type=record_type,
        )

    def add_record(
        self, zone_id: str, record: IDNSRecord[str | None]
    ) -> DNSRecord[str]:
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        data = _record_to_json(record, zone_id=zone_id)
        result, info = self._post(
            "v1/records", data=data, expected=[200, 422], require_json_object=True
        )
        if info["status"] == 422:
            raise DNSAPIError(
                f'The new {record.type} record with value "{record.target}" and TTL {record.ttl}'
                f" has not been accepted by the server{self._extract_only_error_message(result)}"
            )
        return _create_record_from_json(result["record"])

    def update_record(self, zone_id: str, record: DNSRecord[str]) -> DNSRecord[str]:
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to update record!")
        data = _record_to_json(record, zone_id=zone_id)
        result, info = self._put(
            f"v1/records/{record.id}",
            data=data,
            expected=[200, 422],
            require_json_object=True,
        )
        if info["status"] == 422:
            raise DNSAPIError(
                f'The updated {record.type} record with value "{record.target}" and TTL {record.ttl}'
                f" has not been accepted by the server{self._extract_only_error_message(result)}"
            )
        return _create_record_from_json(result["record"])

    def delete_record(self, zone_id: str, record: DNSRecord[str]) -> bool:
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to delete record!")
        dummy, info = self._delete(
            f"v1/records/{record.id}",
            must_have_content=False,
            expected=[200, 404],
        )
        return info["status"] == 200

    @staticmethod
    def _append(results_per_zone_id, zone_id: str, result):
        if zone_id not in results_per_zone_id:
            results_per_zone_id[zone_id] = []
        results_per_zone_id[zone_id].append(result)

    def add_records(
        self,
        records_per_zone_id: Mapping[str, Sequence[IDNSRecord[str | None]]],
        stop_early_on_errors: bool = True,
    ) -> dict[
        str,
        list[
            tuple[DNSRecord[str], t.Literal[True], None]
            | tuple[IDNSRecord[str | None], t.Literal[False], DNSAPIError | None]
        ],
    ]:
        """
        Add new records to an existing zone.

        @param records_per_zone_id: Maps a zone ID to a list of DNS records (DNSRecord)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record, created, failed)``.
                Here ``created`` indicates whether the record was created (``True``) or not (``False``).
                If it was created, ``record`` contains the record ID and ``failed`` is ``None``.
                If it was not created, ``failed`` should be a ``DNSAPIError`` instance indicating why
                it was not created. It is possible that the API only creates records if all succeed,
                in that case ``failed`` can be ``None`` even though ``created`` is ``False``.
        """
        json_records = []
        for zone_id, records in records_per_zone_id.items():
            for record in records:
                json_records.append(_record_to_json(record, zone_id=zone_id))
        data = {"records": json_records}
        # Error 422 means that at least one of the records was not valid
        result, dummy = self._post(
            "v1/records/bulk", data=data, expected=[200, 422], require_json_object=True
        )
        results_per_zone_id: dict[
            str,
            list[
                tuple[DNSRecord[str], t.Literal[True], None]
                | tuple[IDNSRecord[str | None], t.Literal[False], DNSAPIError | None]
            ],
        ] = {}
        # This is the list of invalid records that was detected before accepting the whole set
        for json_record in result.get("invalid_records") or []:
            record = _create_record_from_json(json_record, has_id=False)
            zone_id = json_record["zone_id"]
            self._append(
                results_per_zone_id,
                zone_id,
                (
                    record,
                    False,
                    DNSAPIError(
                        f'Creating {record.type} record "{record.target}" with TTL {record.ttl} for zone {zone_id} failed with unknown reason'
                    ),
                ),
            )
        # This is the list of valid records that were not processed
        for json_record in result.get("valid_records") or []:
            record = _create_record_from_json(json_record, has_id=False)
            zone_id = json_record["zone_id"]
            self._append(results_per_zone_id, zone_id, (record, False, None))
        # This is the list of correctly processed records
        for json_record in result.get("records") or []:
            record = _create_record_from_json(json_record)
            zone_id = json_record["zone_id"]
            self._append(results_per_zone_id, zone_id, (record, True, None))
        return results_per_zone_id

    def update_records(
        self,
        records_per_zone_id: Mapping[str, Sequence[DNSRecord[str]]],
        stop_early_on_errors: bool = True,
    ) -> dict[str, list[tuple[DNSRecord[str], bool, DNSAPIError | None]]]:
        """
        Update multiple records.

        @param records_per_zone_id: Maps a zone ID to a list of DNS records (DNSRecord)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record, updated, failed)``.
                Here ``updated`` indicates whether the record was updated (``True``) or not (``False``).
                If it was not updated, ``failed`` should be a ``DNSAPIError`` instance. If it was
                updated, ``failed`` should be ``None``.  It is possible that the API only updates
                records if all succeed, in that case ``failed`` can be ``None`` even though
                ``updated`` is ``False``.
        """
        # Currently Hetzner's bulk update API seems to be broken, it always returns the error message
        # "An invalid response was received from the upstream server". That's why for now, we always
        # fall back to the default implementation.
        if True:  # pylint: disable=using-constant-test
            return super().update_records(
                records_per_zone_id, stop_early_on_errors=stop_early_on_errors
            )

        json_records = []
        for zone_id, records in records_per_zone_id.items():
            for record in records:
                json_records.append(_record_to_json(record, zone_id=zone_id))
        data = {"records": json_records}
        result, dummy = self._put(
            "v1/records/bulk", data=data, expected=[200], require_json_object=True
        )
        results_per_zone_id = {}
        for json_record in result.get("failed_records") or []:
            record = _create_record_from_json(json_record)
            zone_id = json_record["zone_id"]
            self._append(
                results_per_zone_id,
                zone_id,
                (
                    record,
                    False,
                    DNSAPIError(
                        f'Updating {record.type} record #{record.id} "{record.target}" with TTL {record.ttl} for zone {zone_id} failed with unknown reason'
                    ),
                ),
            )
        for json_record in result.get("records") or []:
            record = _create_record_from_json(json_record)
            zone_id = json_record["zone_id"]
            self._append(results_per_zone_id, zone_id, (record, True, None))
        return results_per_zone_id


def _create_zone_from_new_json(source: dict[str, t.Any]) -> DNSZone[str]:
    info = source.copy()
    # Converting ID to str so both APIs can use same interface
    zone = DNSZone(zone_id=str(info.pop("id")), name=info.pop("name"))
    zone.info = info
    return zone


def _create_record_set_from_new_json(
    source: t.Any, *, record_type: str | None = None
) -> DNSRecordSet[str, str]:
    source = dict(source)
    result: DNSRecordSet[str, str] = DNSRecordSet(
        record_set_id=source.pop("id"), record_type=source.pop("type")
    )
    result.ttl = source.pop("ttl", None)
    name = source.pop("name", None)
    if name == "@":
        name = None
    result.prefix = name
    records = source.pop("records")
    for record in records:
        rec = DNSRecord(
            record_id=result.id, record_type=result.type, target=record["value"]
        )
        rec.prefix = result.prefix
        rec.type = result.type
        rec.ttl = result.ttl
        if record["comment"]:
            rec.extra["comment"] = record["comment"]
        result.records.append(rec)
    source.pop("zone", None)
    result.extra.update(source)
    return result


def _get_creation_json_data(
    record_set: IDNSRecordSet[str | None, str | None],
) -> dict[str, t.Any]:
    return {
        "name": record_set.prefix or "@",
        "type": record_set.type,
        "ttl": record_set.ttl,
        "records": [
            {
                "value": record.target,
                "comment": record.extra.get("comment"),
            }
            for record in record_set.records
        ],
    }


def _get_update_json_data_ttl(
    record_set: IDNSRecordSet[str | None, str | None],
) -> dict[str, t.Any]:
    return {
        "ttl": record_set.ttl,
    }


def _get_update_json_data_value(
    record_set: IDNSRecordSet[str | None, str | None],
) -> dict[str, t.Any]:
    return {
        "records": [
            {
                "value": record.target,
                "comment": record.extra.get("comment"),
            }
            for record in record_set.records
        ],
    }


def _q(value: t.Any) -> str:
    return quote(str(value), safe="@*")


def _get_rrset_url(zone_id: str, prefix: str | None, record_type: str) -> str:
    return f"v1/zones/{_q(zone_id)}/rrsets/{_q(prefix or '@')}/{_q(record_type)}"


def _format_action_error(action_with_error) -> str | None:
    error = action_with_error.get("error")
    if not error:
        return None
    return f"{error['message']} ({error['code']})"


# Number of actions to query together at most
_LIMIT_ACTION_QUERYING = 30


class _HetznerNewAPI(ZoneRecordSetAPI[str, str, str], JSONAPIHelper):
    def __init__(
        self, http_helper, token, api="https://api.hetzner.cloud/", debug=False
    ):
        JSONAPIHelper.__init__(self, http_helper, token, api=api, debug=debug)

    def _create_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
        }

    def _create_post_headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

    def _extract_only_error_message(self, result: dict[str, t.Any]) -> str:
        res = ""
        if isinstance(result.get("error"), dict):
            msg = result["error"]["message"]
            code = result["error"]["code"]
            res = f'{res} with error message "{msg}" (error code {code})'
            if result["error"]["details"]:
                res = f"{res}. Details: {result['error']['details']}"
        return res

    def _extract_error_message(self, result: t.Any | None) -> str:
        if result is None:
            return ""
        if isinstance(result, dict):
            res = self._extract_only_error_message(result)
            if res:
                return res
        return f" with data: {result}"

    def _is_rate_limiting_result(
        self, content: bytes | None, info: dict[str, t.Any]
    ) -> bool | int | float:
        if info["status"] != 429:
            return False
        if content is None:
            return False
        try:
            result = json.loads(content.decode("utf8"))
        except Exception:
            return False
        if not isinstance(result, dict):
            return False
        error = result.get("error")
        if not isinstance(error, dict):
            return False
        status = error.get("code")
        if status != "rate_limit_exceeded":
            return False
        # TODO: is there a hint how much time we should wait?
        # If yes, adjust check_done_delay accordingly!
        return 5

    def _check_error(
        self,
        method: HTTPMethod,
        url: str,
        result: t.Any,
        accepted: Collection[str] | None = None,
    ) -> str | None:
        if not isinstance(result, dict):
            return None
        error = result.get("error")
        if not isinstance(error, dict):
            return None
        status = error.get("code")
        if accepted is not None and status in accepted:
            return status
        more = self._extract_error_message(result)
        raise DNSAPIError(f"{method} {url} resulted in API error {status}{more}")

    @t.overload
    def _list_pagination(
        self,
        url: str,
        data_key: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        block_size: int = 100,
        accept_404: t.Literal[False] = False,
    ) -> list[t.Any]: ...

    @t.overload
    def _list_pagination(
        self,
        url: str,
        data_key: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        block_size: int = 100,
        accept_404: t.Literal[True],
    ) -> list[t.Any] | None: ...

    def _list_pagination(
        self,
        url: str,
        data_key: str,
        *,
        query: dict[str, str] | Sequence[tuple[str, str]] | None = None,
        block_size: int = 100,
        accept_404: bool = False,
    ) -> list[t.Any] | None:
        result = []
        page = 1
        while True:
            query_ = _pagination_query(query, block_size=block_size, page=page)
            res, info = self._get(
                url,
                query=query_,
                must_have_content=[200],
                expected=[200, 404] if accept_404 and page == 1 else [200],
                require_json_object=True,
            )
            if accept_404 and page == 1 and info["status"] == 404:
                return None
            self._check_error(
                "GET",
                url,
                res,
                accepted=["not_found"] if accept_404 and page == 1 else [],
            )
            if not isinstance(res, Mapping):
                raise DNSAPIError(
                    f"GET {url} with query parameters {query_} did not result in JSON object, but {type(res)}"
                )
            result.extend(res[data_key])
            if not isinstance(res.get("meta"), dict) and page == 1:
                return result
            if page >= res["meta"]["pagination"]["last_page"]:
                return result
            page += 1

    def get_zone_by_name(self, name: str) -> DNSZone[str] | None:
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        url = f"v1/zones/{_q(name)}"
        result, _info = self._get(url, expected=[200, 404], require_json_object=True)
        if self._check_error("GET", url, result, accepted=["not_found"]) == "not_found":
            return None
        return _create_zone_from_new_json(result["zone"])

    def get_zone_by_id(self, zone_id: str) -> DNSZone[str] | None:
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        return self.get_zone_by_name(str(zone_id))

    def _get_record_set(
        self, zone_id: str, prefix: str | None, record_type: str
    ) -> DNSRecordSet[str, str] | None:
        url = _get_rrset_url(zone_id, prefix, record_type)
        result, _info = self._get(url, expected=[200, 404], require_json_object=True)
        if self._check_error("GET", url, result, accepted=["not_found"]) == "not_found":
            return None
        return _create_record_set_from_new_json(result["rrset"])

    def get_zone_record_sets(
        self,
        zone_id: str,
        prefix: str | None | NotProvidedType = NOT_PROVIDED,
        record_type: str | NotProvidedType = NOT_PROVIDED,
    ) -> list[DNSRecordSet[str, str]] | None:
        """
        Given a zone ID, return a list of record sets, optionally filtered by the provided criteria.

        @param zone_id: The zone ID
        @param prefix: The prefix to filter for, if provided. Since None is a valid value,
                       the special constant NOT_PROVIDED indicates that we are not filtering.
        @param record_type: The record type to filter for, if provided
        @return A list of DNSrecordSet objects, or None if zone was not found
        """
        query: dict[str, str] = {}
        if prefix is not NOT_PROVIDED:
            query["name"] = prefix or "@"  # type: ignore  # This is a string
        if record_type is not NOT_PROVIDED:
            query["type"] = record_type  # type: ignore  # This is a string
        rrsets = self._list_pagination(
            f"v1/zones/{_q(zone_id)}/rrsets",
            "rrsets",
            query=query,
            accept_404=True,
        )
        if rrsets is None:
            return None
        return filter_record_sets(
            [_create_record_set_from_new_json(rrset) for rrset in rrsets],
            prefix=prefix,
            record_type=record_type,
        )

    def _wait_for_actions(
        self,
        actions: list[dict[str, t.Any]],
        what: str,
        *,
        fail_on_error: bool = True,
        stop_on_first_error: bool = False,
    ) -> tuple[list[dict[str, t.Any]], list[dict[str, t.Any]]]:
        errors: list[dict[str, t.Any]] = []
        other_actions: list[dict[str, t.Any]] = []
        # Only do an initial wait if there have been at most _LIMIT_ACTION_QUERYING/2 calls.
        # (This is a heuristic to avoid unnecessary waits when we can already clear the list.)
        do_wait = 2 * len(actions) <= _LIMIT_ACTION_QUERYING
        while True:
            new_errors = [action for action in actions if action["status"] == "error"]
            if new_errors:
                errors.extend(new_errors)
                if stop_on_first_error:
                    break
            other_actions.extend(
                action for action in actions if action["status"] != "running"
            )
            actions = [action for action in actions if action["status"] == "running"]
            if not actions:
                break
            if do_wait:
                time.sleep(1)
            do_wait = True
            action_ids = [str(action["id"]) for action in actions]
            if len(action_ids) == 1:
                url = f"v1/actions/{_q(action_ids[0])}"
                result, dummy = self._get(url, expected=[200], require_json_object=True)
                self._check_error("GET", url, result)
                actions = [result["action"]]
            else:
                remaining_actions = []
                if len(action_ids) > _LIMIT_ACTION_QUERYING:
                    action_ids = action_ids[:_LIMIT_ACTION_QUERYING]
                    remaining_actions = actions[_LIMIT_ACTION_QUERYING:]
                url = "v1/actions"
                result, dummy = self._get(
                    url,
                    query=[("id", action_id) for action_id in sorted(action_ids)],
                    expected=[200],
                    require_json_object=True,
                )
                self._check_error("GET", url, result)
                actions = result["actions"]
                if all(action["status"] != "running" for action in actions):
                    # If all actions queried by this request have stopped, don't wait before querying more
                    do_wait = False
                actions.extend(remaining_actions)
        if errors and fail_on_error:
            error_messages = [_format_action_error(error) for error in errors]
            joined_msgs = ", ".join(msg for msg in error_messages if msg) or "unknown"
            raise DNSAPIError(f"Error while {what}: {joined_msgs}")
        return errors, other_actions + actions

    def add_record_set(
        self,
        zone_id: str,
        record_set: IDNSRecordSet[str | None, str | None],
    ) -> DNSRecordSet[str, str]:
        """
        Adds a new record set to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record set (DNSRecordSet)
        @return The created DNS record set (DNSRecordSet)
        """
        data = _get_creation_json_data(record_set)
        url = f"v1/zones/{_q(zone_id)}/rrsets"
        result, dummy = self._post(
            url, data=data, expected=[201], require_json_object=True
        )
        self._check_error("POST", url, result)
        self._wait_for_actions([result["action"]], "adding record set")
        return _create_record_set_from_new_json(result["rrset"])

    def update_record_set(
        self,
        zone_id: str,
        record_set: DNSRecordSet[str, str],
        updated_records: bool = True,
        updated_ttl: bool = True,
    ) -> DNSRecordSet[str, str]:
        """
        Update a record set.

        @param zone_id: The zone ID
        @param record_set: The DNS record set (DNSRecordSet)
        @param updated_records: Hint whether the values were updated.
        @param updated_ttl: Hint whether the values were updated.
        @return The DNS record set (DNSRecordSet)
        """
        actions = []
        base_url = _get_rrset_url(zone_id, record_set.prefix, record_set.type)
        if updated_ttl:
            data = _get_update_json_data_ttl(record_set)
            url = f"{base_url}/actions/change_ttl"
            ttl_result, dummy = self._post(
                url, data=data, expected=[201], require_json_object=True
            )
            self._check_error("POST", url, ttl_result)
            actions.append(ttl_result["action"])
        if updated_records:
            data = _get_update_json_data_value(record_set)
            url = f"{base_url}/actions/set_records"
            set_result, dummy = self._post(
                url, data=data, expected=[201], require_json_object=True
            )
            self._check_error("POST", url, set_result)
            actions.append(set_result["action"])
        self._wait_for_actions(actions, "changing record set")
        result = self._get_record_set(zone_id, record_set.prefix, record_set.type)
        # If the record set suddenly vanished, return the one we *wanted* to have
        return result if result else record_set

    def delete_record_set(
        self, zone_id: str, record_set: DNSRecordSet[str, str]
    ) -> bool:
        """
        Delete a record set.

        @param zone_id: The zone ID
        @param record_set: The DNS record set (DNSRecordSet)
        @return True in case of success (boolean)
        """
        url = _get_rrset_url(zone_id, record_set.prefix, record_set.type)
        result, _info = self._delete(url, expected=[201, 404], require_json_object=True)
        if (
            self._check_error("DELETE", url, result, accepted=["not_found"])
            == "not_found"
        ):
            return False
        self._wait_for_actions([result["action"]], "deleting record set")
        return True

    def _fetch_all_records(
        self, zone_id: str, prefixes_and_types: Sequence[tuple[str | None, str]]
    ) -> list[DNSRecordSet[str, str]]:
        if not prefixes_and_types:
            return []
        common_prefix: str | None | NotProvidedType
        common_type: str | NotProvidedType
        common_prefix, common_type = prefixes_and_types[0]
        if len(prefixes_and_types) == 1:
            res = self._get_record_set(zone_id, common_prefix, common_type)
            return [res] if res else []
        if any(common_prefix != prefix for prefix, _r_type in prefixes_and_types):
            common_prefix = NOT_PROVIDED
        if any(common_type != r_type for _prefix, r_type in prefixes_and_types):
            common_type = NOT_PROVIDED
        return (
            self.get_zone_record_sets(
                zone_id, prefix=common_prefix, record_type=common_type
            )
            or []
        )

    @t.overload
    def _collect_results(
        self,
        what: str,
        data_per_zone_id: dict[
            str,
            list[
                tuple[DNSRecordSet[str, str], list[str], None]
                | tuple[
                    IDNSRecordSet[str | None, str | None],
                    None,
                    DNSAPIError,
                ]
            ],
        ],
        actions: dict[t.Any, dict[str, t.Any]],
        *,
        do_wait: bool,
        stop_early_on_errors: bool,
        refresh_rrsets: bool = True,
        has_incomplete: t.Literal[True],
    ) -> dict[
        str,
        list[
            tuple[DNSRecordSet[str, str], t.Literal[True], None]
            | tuple[
                IDNSRecordSet[str | None, str | None],
                t.Literal[False],
                DNSAPIError | None,
            ]
        ],
    ]: ...

    @t.overload
    def _collect_results(
        self,
        what: str,
        data_per_zone_id: dict[
            str,
            list[tuple[DNSRecordSet[str, str], list[str] | None, DNSAPIError | None]],
        ],
        actions: dict[t.Any, dict[str, t.Any]],
        *,
        do_wait: bool,
        stop_early_on_errors: bool,
        refresh_rrsets: bool = True,
        has_incomplete: t.Literal[False],
    ) -> dict[
        str,
        list[tuple[DNSRecordSet[str, str], bool, DNSAPIError | None]],
    ]: ...

    def _collect_results(
        self,
        what: str,
        data_per_zone_id: Mapping[
            str,
            Sequence[
                tuple[
                    DNSRecordSet[str, str] | IDNSRecordSet[str | None, str | None],
                    list[str] | None,
                    DNSAPIError | None,
                ]
            ],
        ],
        actions: dict[t.Any, dict[str, t.Any]],
        *,
        do_wait: bool,
        stop_early_on_errors: bool,
        refresh_rrsets: bool = True,
        has_incomplete: bool,
    ) -> dict[str, list[t.Any]]:
        errors = {}
        if do_wait:
            action_errors, _other_actions = self._wait_for_actions(
                list(actions.values()),
                what,
                fail_on_error=False,
                stop_on_first_error=stop_early_on_errors,
            )
            for action_error in action_errors:
                errors[action_error["id"]] = DNSAPIError(
                    _format_action_error(action_error)
                )
        results_per_zone_id = {}
        for zone_id, datas in data_per_zone_id.items():
            result: list[
                tuple[
                    DNSRecordSet[str, str] | IDNSRecordSet[str | None, str | None],
                    bool,
                    DNSAPIError | None,
                ]
            ] = []
            results_per_zone_id[zone_id] = result
            refresh = {}
            for record_set, action_ids, error in datas:
                if error is not None:
                    result.append((record_set, False, error))
                error = None
                rr_errors = [
                    errors[action_id]
                    for action_id in action_ids or []
                    if action_id in errors
                ]
                if rr_errors:
                    # If there are multiple ones, only use the first
                    result.append((record_set, False, rr_errors[0]))
                else:
                    # Need to refresh this record set
                    refresh[(record_set.prefix, record_set.type)] = len(result)
                    result.append((record_set, True, None))
            if refresh_rrsets:
                for record_set in self._fetch_all_records(
                    zone_id, list(refresh.keys())
                ):
                    index = refresh.get((record_set.prefix, record_set.type))
                    if index is not None:
                        result[index] = (record_set, True, None)
        return results_per_zone_id

    def add_record_sets(
        self,
        record_sets_per_zone_id: Mapping[
            str, Sequence[IDNSRecordSet[str | None, str | None]]
        ],
        stop_early_on_errors: bool = True,
    ) -> dict[
        str,
        list[
            tuple[DNSRecordSet[str, str], t.Literal[True], None]
            | tuple[
                IDNSRecordSet[str | None, str | None],
                t.Literal[False],
                DNSAPIError | None,
            ]
        ],
    ]:
        """
        Add new record sets to an existing zone.

        @param record_sets_per_zone_id: Maps a zone ID to a list of DNS record sets (DNSRecordSet)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, created, failed)``.
                Here ``created`` indicates whether the record set was created (``True``) or not (``False``).
                If it was created, ``record_set`` contains the record set ID and ``failed`` is ``None``.
                If it was not created, ``failed`` should be a ``DNSAPIError`` instance indicating why
                it was not created. It is possible that the API only creates record sets if all succeed,
                in that case ``failed`` can be ``None`` even though ``created`` is ``False``.
        """
        actions = {}
        data_per_zone_id = {}
        stop = False
        for zone_id, record_sets in record_sets_per_zone_id.items():
            data: list[
                tuple[DNSRecordSet[str, str], list[str], None]
                | tuple[
                    IDNSRecordSet[str | None, str | None],
                    None,
                    DNSAPIError,
                ]
            ] = []
            data_per_zone_id[zone_id] = data
            for record_set in record_sets:
                creation_data = _get_creation_json_data(record_set)
                try:
                    url = f"v1/zones/{_q(zone_id)}/rrsets"
                    res, dummy = self._post(
                        url,
                        data=creation_data,
                        expected=[201],
                        require_json_object=True,
                    )
                    self._check_error("POST", url, res)
                    action = res["action"]
                    actions[action["id"]] = action
                    data.append(
                        (
                            _create_record_set_from_new_json(res["rrset"]),
                            [action["id"]],
                            None,
                        )
                    )
                except DNSAPIError as e:
                    data.append((record_set, None, e))
                    if stop_early_on_errors:
                        stop = True
                        break
            if stop:
                break
        return self._collect_results(
            "adding record sets",
            data_per_zone_id,
            actions,
            do_wait=not stop,
            stop_early_on_errors=stop_early_on_errors,
            refresh_rrsets=False,
            has_incomplete=True,
        )

    def update_record_sets(
        self,
        record_sets_per_zone_id: Mapping[
            str, Sequence[tuple[DNSRecordSet[str, str], bool, bool]]
        ],
        stop_early_on_errors: bool = True,
    ) -> dict[
        str,
        list[tuple[DNSRecordSet[str, str], bool, DNSAPIError | None]],
    ]:
        """
        Update multiple record sets.

        @param record_sets_per_zone_id: Maps a zone ID to a list of tuples
                                        (record_set, updated_records, updated_ttl)
                                        of type (DNSRecordSet, bool, bool).
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, updated, failed)``.
                Here ``updated`` indicates whether the record set was updated (``True``) or not (``False``).
                If it was not updated, ``failed`` should be a ``DNSAPIError`` instance. If it was
                updated, ``failed`` should be ``None``.  It is possible that the API only updates
                record sets if all succeed, in that case ``failed`` can be ``None`` even though
                ``updated`` is ``False``.
        """
        actions = {}
        data_per_zone_id = {}
        stop = False
        for zone_id, record_sets in record_sets_per_zone_id.items():
            data: list[
                tuple[DNSRecordSet[str, str], list[str] | None, DNSAPIError | None]
            ] = []
            data_per_zone_id[zone_id] = data
            for record_set, updated_records, updated_ttl in record_sets:
                base_url = _get_rrset_url(zone_id, record_set.prefix, record_set.type)
                try:
                    action_ids = []
                    if updated_ttl:
                        ttl_data = _get_update_json_data_ttl(record_set)
                        ttl_url = f"{base_url}/actions/change_ttl"
                        ttl_result, dummy = self._post(
                            ttl_url,
                            data=ttl_data,
                            expected=[201],
                            require_json_object=True,
                        )
                        self._check_error("POST", ttl_url, ttl_result)
                        action = ttl_result["action"]
                        action_id = action["id"]
                        actions[action_id] = action
                        action_ids.append(action_id)
                    if updated_records:
                        set_data = _get_update_json_data_value(record_set)
                        set_url = f"{base_url}/actions/set_records"
                        set_result, dummy = self._post(
                            set_url,
                            data=set_data,
                            expected=[201],
                            require_json_object=True,
                        )
                        self._check_error("POST", set_url, set_result)
                        action = set_result["action"]
                        action_id = action["id"]
                        actions[action_id] = action
                        action_ids.append(action_id)
                    data.append((record_set, action_ids, None))
                except DNSAPIError as e:
                    data.append((record_set, None, e))
                    if stop_early_on_errors:
                        stop = True
                        break
            if stop:
                break
        return self._collect_results(
            "updating record sets",
            data_per_zone_id,
            actions,
            do_wait=not stop,
            stop_early_on_errors=stop_early_on_errors,
            refresh_rrsets=not stop,
            has_incomplete=False,
        )

    def delete_record_sets(
        self,
        record_sets_per_zone_id: Mapping[str, Sequence[DNSRecordSet[str, str]]],
        stop_early_on_errors: bool = True,
    ) -> dict[
        str,
        list[tuple[DNSRecordSet[str, str], bool, DNSAPIError | None]],
    ]:
        """
        Delete multiple record_sets.

        @param record_sets_per_zone_id: Maps a zone ID to a list of DNS record sets (DNSRecordSet)
        @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                     This might only work on some APIs.
        @return A dictionary mapping zone IDs to lists of tuples ``(record_set, deleted, failed)``.
                In case ``record_set`` was deleted or not deleted, ``deleted`` is ``True``
                respectively ``False``, and ``failed`` is ``None``. In case an error happened
                while deleting, ``deleted`` is ``False`` and ``failed`` is a ``DNSAPIError``
                instance hopefully providing information on the error.
        """
        actions = {}
        data_per_zone_id = {}
        stop = False
        for zone_id, record_sets in record_sets_per_zone_id.items():
            data: list[
                tuple[DNSRecordSet[str, str], list[str] | None, DNSAPIError | None]
            ] = []
            data_per_zone_id[zone_id] = data
            for record_set in record_sets:
                try:
                    url = _get_rrset_url(zone_id, record_set.prefix, record_set.type)
                    result, _info = self._delete(
                        url, expected=[201, 404], require_json_object=True
                    )
                    if (
                        self._check_error("DELETE", url, result, accepted=["not_found"])
                        == "not_found"
                    ):
                        data.append((record_set, None, None))
                    else:
                        action = result["action"]
                        actions[action["id"]] = action
                        data.append((record_set, [action["id"]], None))
                except DNSAPIError as e:
                    data.append((record_set, None, e))
                    if stop_early_on_errors:
                        stop = True
                        break
            if stop:
                break
        return self._collect_results(
            "deleting record sets",
            data_per_zone_id,
            actions,
            do_wait=not stop,
            stop_early_on_errors=stop_early_on_errors,
            refresh_rrsets=False,
            has_incomplete=False,
        )


class HetznerProviderInformation(ProviderInformation):
    def __init__(self, option_provider: OptionProvider | None = None) -> None:
        self._api = None
        if option_provider is not None:
            hetzner_token = option_provider.get_option("hetzner_token")
            hetzner_api_token = option_provider.get_option("hetzner_api_token")
            if hetzner_token is not None:
                self._api = "old"
            if hetzner_api_token is not None:
                self._api = "new"

    def get_supported_record_types(self) -> list[str]:
        """
        Return a list of supported record types.
        """
        old_api = [
            "A",
            "AAAA",
            "NS",
            "MX",
            "CNAME",
            "RP",
            "TXT",
            "SOA",
            "HINFO",
            "SRV",
            "TLSA",
            "DS",
            "CAA",
            "DANE",
        ]
        new_api = [
            "A",
            "AAAA",
            "NS",
            "MX",
            "CNAME",
            "RP",
            "TXT",
            "SOA",
            "HINFO",
            "SRV",
            "TLSA",
            "DS",
            "CAA",
            "HTTPS",
            "PTR",
            "SVCB",
        ]
        if self._api == "old":
            return old_api
        if self._api == "new":
            return new_api
        return sorted(set(old_api) | set(new_api))

    def get_zone_id_type(self) -> AnsibleType:
        """
        Return the (short) type for zone IDs, like ``'int'`` or ``'str'``.
        """
        # For the new API, this would be 'int'.
        # Since we have to support both APIs, we're using 'str'.
        return "str"

    def get_record_id_type(self) -> AnsibleType:
        """
        Return the (short) type for record IDs, like ``'int'`` or ``'str'``.
        """
        return "str"

    def get_record_default_ttl(self) -> int | None:
        """
        Return the default TTL for records, like 300, 3600 or None.
        None means that some other TTL (usually from the zone) will be used.
        """
        return None

    def normalize_prefix(self, prefix: str | None) -> str | None:
        """
        Given a prefix (string or None), return its normalized form.

        The result should always be None for the trivial prefix, and a non-zero length DNS name
        for a non-trivial prefix.

        If a provider supports other identifiers for the trivial prefix, such as '@', this
        function needs to convert them to None as well.
        """
        return None if prefix in ("@", "") else prefix

    def supports_bulk_actions(self) -> bool:
        """
        Return whether the API supports some kind of bulk actions.
        """
        return True

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

    def txt_always_quote(self) -> bool:
        """
        Return whether TXT records sent to the API should always be quoted.

        Returns a boolean.

        This return value is only used if txt_record_handling does not return 'decoded'.
        """
        return self._api == "new"


def create_hetzner_provider_information(
    option_provider: OptionProvider | None = None,
) -> HetznerProviderInformation:
    return HetznerProviderInformation(option_provider=option_provider)


def create_hetzner_argument_spec() -> ArgumentSpec:
    return ArgumentSpec(
        argument_spec={
            "hetzner_token": {
                "type": "str",
                "no_log": True,
                "aliases": ["api_token"],
                "fallback": (env_fallback, ["HETZNER_DNS_TOKEN"]),
            },
            "hetzner_api_token": {
                "type": "str",
                "no_log": True,
                "fallback": (env_fallback, ["HETZNER_API_TOKEN"]),
            },
        },
        mutually_exclusive=[["hetzner_token", "hetzner_api_token"]],
        required_one_of=[["hetzner_token", "hetzner_api_token"]],
    )


def create_hetzner_api(
    option_provider: OptionProvider, http_helper: HTTPHelper
) -> HetznerAPI | _HetznerNewAPI:
    hetzner_token = option_provider.get_option("hetzner_token")
    hetzner_api_token = option_provider.get_option("hetzner_api_token")
    if hetzner_token is not None:
        return HetznerAPI(http_helper, hetzner_token)
    if hetzner_api_token is not None:
        return _HetznerNewAPI(http_helper, hetzner_api_token)
    raise AssertionError(
        "One of hetzner_token and hetzner_api_token must be provided"
    )  # pragma: no cover
