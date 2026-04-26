# Copyright (c) 2025 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._record import (
    RecordIDT,
    RecordIDT_co,
)
from ansible_collections.community.dns.plugins.module_utils._record import (
    format_ttl as _format_ttl,
)

if t.TYPE_CHECKING:
    from collections.abc import Mapping, Sequence  # pragma: no cover

    from ._conversion.converter import RecordConverter  # pragma: no cover
    from ._record import DNSRecord, IDNSRecord  # pragma: no cover


RecordSetIDT = t.TypeVar("RecordSetIDT")
RecordSetIDT_co = t.TypeVar("RecordSetIDT_co", covariant=True)


class IDNSRecordSet(t.Protocol, t.Generic[RecordSetIDT_co, RecordIDT_co]):
    @property
    def id(self) -> RecordSetIDT_co: ...

    @property
    def type(self) -> str: ...

    @property
    def prefix(self) -> str | None: ...

    @property
    def ttl(self) -> int | None: ...

    @property
    def records(self) -> Sequence[IDNSRecord[RecordIDT_co]]: ...

    @property
    def extra(self) -> Mapping[str, str]: ...


class DNSRecordSet(t.Generic[RecordSetIDT, RecordIDT]):
    def __init__(self, *, record_set_id: RecordSetIDT, record_type: str) -> None:
        self.id = record_set_id
        self.type = record_type
        self.prefix: str | None = None
        self.ttl: int | None = None
        self.records: list[DNSRecord] = []
        self.extra: dict[str, str] = {}

    def clone(self) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        result: DNSRecordSet[RecordSetIDT, RecordIDT] = DNSRecordSet(
            record_set_id=self.id, record_type=self.type
        )
        result.prefix = self.prefix
        result.records = [record.clone() for record in self.records]
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
        data.append(f"ttl: {_format_ttl(self.ttl)}")
        data.append(f"records: [{', '.join([str(record) for record in self.records])}]")
        if self.extra:
            data.append(f"extra: {self.extra}")
        return "DNSRecordSet(" + ", ".join(data) + ")"

    def __repr__(self) -> str:
        return self.__str__()


def format_record_set_for_output(
    record_set: IDNSRecordSet[RecordSetIDT_co, RecordIDT_co],
    record_name: str | None,
    prefix: str | None = None,
    record_converter: RecordConverter | None = None,
) -> dict[str, t.Any]:
    entry: dict[str, t.Any] = {
        "prefix": prefix or "",
        "type": record_set.type,
        "ttl": record_set.ttl,
        "value": sorted(record.target for record in record_set.records),
    }
    if record_converter:
        entry["value"] = record_converter.process_values_to_user(
            entry["type"], entry["value"]
        )
    if record_name is not None:
        entry["record"] = record_name
    return entry
