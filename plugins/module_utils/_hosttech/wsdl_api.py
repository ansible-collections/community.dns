# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.dns.plugins.module_utils._record import DNSRecord
from ansible_collections.community.dns.plugins.module_utils._wsdl import (
    Composer,
    WSDLError,
    WSDLNetworkError,
)
from ansible_collections.community.dns.plugins.module_utils._zone import (
    DNSZone,
    DNSZoneWithRecords,
)
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    NOT_PROVIDED,
    DNSAPIAuthenticationError,
    DNSAPIError,
    ZoneRecordAPI,
    filter_records,
)

if t.TYPE_CHECKING:
    from .._http import HTTPHelper  # pragma: no cover
    from .._record import IDNSRecord  # pragma: no cover
    from .._zone_record_api import NotProvidedType  # pragma: no cover

    _T = t.TypeVar("_T")  # pragma: no cover


def _create_record_from_encoding(
    source: dict[str, t.Any], record_type: str | None = None
) -> DNSRecord[int]:
    source = dict(source)
    record_type = source.pop("type", record_type)
    if record_type is None:
        raise DNSAPIError("Record from API has no type")

    priority = source.pop("priority")
    target: str = source.pop("target")
    if record_type in ("PTR", "MX"):
        target = f"{priority} {target}"

    result = DNSRecord(
        record_id=source.pop("id"), record_type=record_type, target=target
    )
    result.prefix = source.pop("prefix", None)
    ttl = source.pop("ttl")
    result.ttl = int(ttl) if ttl is not None else None
    source.pop("zone", None)
    result.extra["comment"] = source.pop("comment") or ""
    result.extra.update(source)
    return result


def _create_zone_from_encoding(
    source: dict[str, t.Any],
    prefix: str | None | NotProvidedType = NOT_PROVIDED,
    record_type: str | NotProvidedType = NOT_PROVIDED,
) -> DNSZoneWithRecords[int, int]:
    zone = DNSZone(zone_id=source["id"], name=source["name"])
    zone.info = {
        "email": source.get("email"),
        "ttl": source["ttl"],
    }
    return DNSZoneWithRecords(
        zone,
        filter_records(
            [_create_record_from_encoding(record) for record in source["records"]],
            prefix=prefix,
            record_type=record_type,
        ),
    )


def _encode_record(
    record: IDNSRecord[int | None], include_id: bool = False
) -> dict[str, t.Any]:
    result: dict[str, t.Any] = {
        "type": record.type,
        "prefix": record.prefix,
        "target": record.target,
        "ttl": record.ttl,
    }
    if record.type in ("PTR", "MX"):
        try:
            priority, target = record.target.split(" ", 1)
            result["priority"] = int(priority)
            result["target"] = target
        except Exception as e:
            raise DNSAPIError(
                f'Cannot split {record.type} record "{record.target}" into integer priority and target: {e}'
            ) from e
    else:
        result["priority"] = None
    if include_id:
        result["id"] = record.id
    return result


class HostTechWSDLAPI(ZoneRecordAPI[int, int]):
    def __init__(
        self,
        http_helper: HTTPHelper,
        username: str,
        password: str,
        api: str = "https://ns1.hosttech.eu/public/api",
        debug: bool = False,
    ) -> None:
        """
        Create a new HostTech API instance with given username and password.
        """
        self._http_helper = http_helper
        self._api = api
        self._namespaces = {
            "ns1": "https://ns1.hosttech.eu/soap",
        }
        self._username = username
        self._password = password
        self._debug = debug

    def _prepare(self) -> Composer:
        command = Composer(self._http_helper, self._api, self._namespaces)
        command.add_auth(self._username, self._password)
        return command

    def _announce(self, msg: str) -> None:
        if self._debug:
            pass  # pragma: no cover
            # q.q('{0} {1} {2}'.format('=' * 4, msg, '=' * 40))

    def _execute(
        self, command: Composer, result_name: str, acceptable_type: type[_T]
    ) -> _T:
        if self._debug:
            pass  # pragma: no cover
            # q.q('Request: {0}'.format(command))
        try:
            result = command.execute(debug=self._debug)
        except WSDLError as e:
            if e.error_code == "998":
                raise DNSAPIAuthenticationError(
                    f"Error on authentication ({e.error_message})"
                ) from e
            raise
        res = result.get_result(result_name)
        if isinstance(res, acceptable_type):
            if self._debug:
                pass  # pragma: no cover
                # q.q('Extracted result: {0} (type {1})'.format(res, type(res)))
            return res
        if self._debug:
            pass  # pragma: no cover
            # q.q('Result: {0}; extracted type {1}'.format(result, type(res)))
        raise DNSAPIError(
            f"Result has unexpected type {type(res)} (expecting {acceptable_type})!"
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
        self._announce("get zone")
        command = self._prepare()
        command.add_simple_command("getZone", sZoneName=name)
        try:
            return _create_zone_from_encoding(
                self._execute(command, "getZoneResponse", dict),
                prefix=prefix,
                record_type=record_type,
            )
        except WSDLError as exc:
            if exc.error_origin == "server" and exc.error_message == "zone not found":
                return None
            raise DNSAPIError(f"Error while getting zone: {to_native(exc)}") from exc
        except WSDLNetworkError as exc:
            raise DNSAPIError(
                f"Network error while getting zone: {to_native(exc)}"
            ) from exc

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
        return self.get_zone_with_records_by_name(
            str(zone_id), prefix=prefix, record_type=record_type
        )

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
        result = self.get_zone_with_records_by_id(
            zone_id, prefix=prefix, record_type=record_type
        )
        return result.records if result is not None else None

    def get_zone_by_name(self, name: str) -> DNSZone[int] | None:
        """
        Given a zone name, return the zone contents if found.

        @param name: The zone name (string)
        @return The zone information (DNSZone), or None if not found
        """
        zone = self.get_zone_with_records_by_name(name)
        return zone.zone if zone else None

    def get_zone_by_id(self, zone_id: int) -> DNSZone[int] | None:
        """
        Given a zone ID, return the zone contents if found.

        @param zone_id: The zone ID
        @return The zone information (DNSZone), or None if not found
        """
        zone = self.get_zone_with_records_by_id(zone_id)
        return zone.zone if zone else None

    def add_record(
        self, zone_id: int, record: IDNSRecord[int | None]
    ) -> DNSRecord[int]:
        """
        Adds a new record to an existing zone.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The created DNS record (DNSRecord)
        """
        self._announce("add record")
        command = self._prepare()
        command.add_simple_command(
            "addRecord",
            search=str(zone_id),
            recorddata=_encode_record(record, include_id=False),
        )
        try:
            return _create_record_from_encoding(
                self._execute(command, "addRecordResponse", dict)
            )
        except WSDLError as exc:
            raise DNSAPIError(f"Error while adding record: {to_native(exc)}") from exc
        except WSDLNetworkError as exc:
            raise DNSAPIError(
                f"Network error while adding record: {to_native(exc)}"
            ) from exc

    def update_record(self, zone_id: int, record: DNSRecord[int]) -> DNSRecord[int]:
        """
        Update a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return The DNS record (DNSRecord)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to update record!")
        self._announce("update record")
        command = self._prepare()
        command.add_simple_command(
            "updateRecord",
            recordId=record.id,
            recorddata=_encode_record(record, include_id=False),
        )
        try:
            return _create_record_from_encoding(
                self._execute(command, "updateRecordResponse", dict)
            )
        except WSDLError as exc:
            raise DNSAPIError(f"Error while updating record: {to_native(exc)}") from exc
        except WSDLNetworkError as exc:
            raise DNSAPIError(
                f"Network error while updating record: {to_native(exc)}"
            ) from exc

    def delete_record(self, zone_id: int, record: DNSRecord[int]) -> bool:
        """
        Delete a record.

        @param zone_id: The zone ID
        @param record: The DNS record (DNSRecord)
        @return True in case of success (boolean)
        """
        if record.id is None:
            raise DNSAPIError("Need record ID to delete record!")
        self._announce("delete record")
        command = self._prepare()
        command.add_simple_command("deleteRecord", recordId=record.id)
        try:
            return self._execute(command, "deleteRecordResponse", bool)
        except WSDLError as exc:
            raise DNSAPIError(f"Error while deleting record: {to_native(exc)}") from exc
        except WSDLNetworkError as exc:
            raise DNSAPIError(
                f"Network error while deleting record: {to_native(exc)}"
            ) from exc
