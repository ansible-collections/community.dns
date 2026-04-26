# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._record import RecordIDT
from ansible_collections.community.dns.plugins.module_utils._record_set import (
    RecordSetIDT,
)

if t.TYPE_CHECKING:
    from collections.abc import Mapping  # pragma: no cover

    from ._record import DNSRecord  # pragma: no cover
    from ._record_set import DNSRecordSet  # pragma: no cover


ZoneIDT = t.TypeVar("ZoneIDT")
ZoneIDT_co = t.TypeVar("ZoneIDT_co", covariant=True)


class IDNSZone(t.Protocol, t.Generic[ZoneIDT_co]):
    @property
    def id(self) -> ZoneIDT_co: ...

    @property
    def name(self) -> str: ...

    @property
    def info(self) -> Mapping[str, t.Any]: ...


class DNSZone(t.Generic[ZoneIDT]):
    def __init__(
        self,
        *,
        zone_id: ZoneIDT,
        name: str,
        info: dict[str, t.Any] | None = None,
    ) -> None:
        self.id = zone_id
        self.name = name
        self.info: dict[str, t.Any] = info or {}

    def __str__(self) -> str:
        data = []
        if self.id is not None:
            data.append(f"id: {self.id}")
        data.append(f"name: {self.name}")
        data.append(f"info: {self.info}")
        return "DNSZone(" + ", ".join(data) + ")"

    def __repr__(self) -> str:
        return self.__str__()


class DNSZoneWithRecords(t.Generic[ZoneIDT, RecordIDT]):
    def __init__(
        self,
        zone: DNSZone[ZoneIDT],
        records: list[DNSRecord[RecordIDT]],
    ) -> None:
        self.zone = zone
        self.records = records

    def __str__(self) -> str:
        return f"({self.zone}, {self.records})"

    def __repr__(self) -> str:
        return f"DNSZoneWithRecords({self.zone!r}, {self.records!r})"


class DNSZoneWithRecordSets(t.Generic[ZoneIDT, RecordSetIDT, RecordIDT]):
    def __init__(
        self,
        zone: DNSZone[ZoneIDT],
        record_sets: list[DNSRecordSet[RecordSetIDT, RecordIDT]],
    ) -> None:
        self.zone = zone
        self.record_sets = record_sets

    def __str__(self) -> str:
        return f"({self.zone}, {self.record_sets})"

    def __repr__(self) -> str:
        return f"DNSZoneWithRecordSets({self.zone!r}, {self.record_sets!r})"
