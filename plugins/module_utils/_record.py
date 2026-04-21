# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations


def format_ttl(ttl):
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


class DNSRecord:
    def __init__(self):
        self.id = None
        self.type = None
        self.prefix = None
        self.target = None
        self.ttl = 86400  # 24 * 60 * 60
        self.extra = {}

    def clone(self):
        result = DNSRecord()
        result.id = self.id
        result.type = self.type
        result.prefix = self.prefix
        result.target = self.target
        result.ttl = self.ttl
        result.extra = dict(self.extra)
        return result

    def __str__(self):
        data = []
        if self.id:
            data.append(f"id: {self.id}")
        data.append(f"type: {self.type}")
        if self.prefix:
            data.append(f'prefix: "{self.prefix}"')
        else:
            data.append("prefix: (none)")
        data.append(f'target: "{self.target}"')
        data.append(f"ttl: {format_ttl(self.ttl)}")
        if self.extra:
            data.append(f"extra: {self.extra}")
        return "DNSRecord(" + ", ".join(data) + ")"

    def __repr__(self):
        return self.__str__()


def sorted_ttls(ttls):
    return sorted(ttls, key=lambda ttl: 0 if ttl is None else ttl)


def format_records_for_output(records, record_name, prefix=None, record_converter=None):
    ttls = sorted_ttls({record.ttl for record in records})
    entry = {
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


def format_record_for_output(record, record_name, prefix=None, record_converter=None):
    entry = {
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
