# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

if t.TYPE_CHECKING:
    from ._record import DNSRecord  # pragma: no cover
    from ._record_set import DNSRecordSet  # pragma: no cover


class DNSZone:
    def __init__(
        self,
        name: str,
        info: dict[str, t.Any] | None = None,
    ) -> None:
        self.id: str | None = None
        self.name = name
        self.info: dict[str, t.Any] = info or {}

    def __str__(self) -> str:
        data = []
        if self.id is not None:
            data.append("id: {0}".format(self.id))
        data.append("name: {0}".format(self.name))
        data.append("info: {0}".format(self.info))
        return "DNSZone(" + ", ".join(data) + ")"

    def __repr__(self) -> str:
        return self.__str__()


class DNSZoneWithRecords:
    def __init__(
        self,
        zone: DNSZone,
        records: list[DNSRecord],
    ) -> None:
        self.zone = zone
        self.records = records

    def __str__(self) -> str:
        return "({0}, {1})".format(self.zone, self.records)

    def __repr__(self) -> str:
        return "DNSZoneWithRecords({0!r}, {1!r})".format(self.zone, self.records)


class DNSZoneWithRecordSets:
    def __init__(
        self,
        zone: DNSZone,
        record_sets: list[DNSRecordSet],
    ) -> None:
        self.zone = zone
        self.record_sets = record_sets

    def __str__(self) -> str:
        return "({0}, {1})".format(self.zone, self.record_sets)

    def __repr__(self) -> str:
        return "DNSZoneWithRecordSets({0!r}, {1!r})".format(self.zone, self.record_sets)
