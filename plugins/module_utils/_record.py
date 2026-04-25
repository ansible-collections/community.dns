# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence  # pragma: no cover

    from ._conversion.converter import RecordConverter  # pragma: no cover


def format_ttl(ttl: int | None) -> str:
    if ttl is None:
        return "default"
    sec = ttl % 60
    ttl //= 60
    mins = ttl % 60
    ttl //= 60
    h = ttl
    result = []
    if h:
        result.append(f"{h}h")
    if mins:
        result.append(f"{mins}m")
    if sec:
        result.append(f"{sec}s")
    return " ".join(result)


RecordIDT = t.TypeVar("RecordIDT")
RecordIDT_co = t.TypeVar("RecordIDT_co", covariant=True)


class IDNSRecord(t.Protocol, t.Generic[RecordIDT_co]):
    @property
    def id(self) -> RecordIDT_co: ...

    @property
    def type(self) -> str: ...

    @property
    def prefix(self) -> str | None: ...

    @property
    def target(self) -> str: ...

    @property
    def ttl(self) -> int | None: ...

    @property
    def extra(self) -> Mapping[str, str]: ...


class DNSRecord(t.Generic[RecordIDT]):
    def __init__(self, *, record_id: RecordIDT, record_type: str, target: str) -> None:
        self.id = record_id
        self.type = record_type
        self.prefix: str | None = None
        self.target = target
        self.ttl: int | None = 86400  # 24 * 60 * 60
        self.extra: dict[str, str] = {}

    def clone(self) -> DNSRecord[RecordIDT]:
        result = DNSRecord(record_id=self.id, record_type=self.type, target=self.target)
        result.prefix = self.prefix
        result.ttl = self.ttl
        result.extra = dict(self.extra)
        return result

    def __str__(self) -> str:
        data = []
        if self.id is not None:
            data.append(f"id: {self.id}")
        data.append(f"type: {self.type}")
        if self.prefix is not None:
            data.append(f"prefix: {self.prefix!r}")
        else:
            data.append("prefix: (none)")
        data.append(f"target: {self.target!r}")
        data.append(f"ttl: {format_ttl(self.ttl)}")
        if self.extra:
            data.append(f"extra: {self.extra}")
        return "DNSRecord(" + ", ".join(data) + ")"

    def __repr__(self) -> str:
        return self.__str__()


@t.overload
def sorted_ttls(ttls: Collection[int]) -> list[int]: ...


@t.overload
def sorted_ttls(ttls: Collection[int | None]) -> list[int | None]: ...


def sorted_ttls(ttls: Collection[int | None]) -> list[int | None] | list[int]:
    return sorted(ttls, key=lambda ttl: 0 if ttl is None else ttl)


def format_records_for_output(
    records: Sequence[IDNSRecord[RecordIDT_co]],
    record_name: str | None,
    prefix: str | None = None,
    record_converter: RecordConverter | None = None,
) -> dict[str, t.Any]:
    ttls = sorted_ttls({record.ttl for record in records})
    entry: dict[str, t.Any] = {
        "prefix": prefix or "",
        "type": min(record.type for record in records) if records else None,
        "ttl": ttls[0] if len(ttls) > 0 else None,
        "value": [record.target for record in records],
    }
    if record_converter:
        entry["value"] = record_converter.process_values_to_user(
            entry["type"], entry["value"]
        )
    if record_name is not None:
        entry["record"] = record_name
    if len(ttls) > 1:
        entry["ttls"] = ttls
    return entry


def format_record_for_output(
    record: IDNSRecord[RecordIDT_co],
    record_name: str | None,
    prefix: str | None = None,
    record_converter: RecordConverter | None = None,
) -> dict[str, t.Any]:
    entry: dict[str, t.Any] = {
        "prefix": prefix or "",
        "type": record.type,
        "ttl": record.ttl,
        "value": record.target,
        "extra": record.extra,
    }
    if record_converter:
        entry["value"] = record_converter.process_value_to_user(
            entry["type"], entry["value"]
        )
    if record_name is not None:
        entry["record"] = record_name
    return entry
