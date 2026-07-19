# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._argspec import (
    ArgumentSpec,
)
from ansible_collections.community.dns.plugins.module_utils._names import (
    join_labels,
    normalize_label,
    split_into_labels,
)
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    NOT_PROVIDED,
    DNSAPIError,
)

if t.TYPE_CHECKING:  # pragma: no cover
    from .._provider import ProviderInformation
    from .._zone_record_api import NotProvidedType


def create_zone_name_id_argspec(
    provider_information: ProviderInformation,
) -> ArgumentSpec:
    if provider_information.is_zone_id_equal_to_zone_name():
        return ArgumentSpec(
            argument_spec={
                "zone_name": {
                    "type": "str",
                    "aliases": ["zone", "zone_id"],
                    "required": True,
                },
            },
        )
    return ArgumentSpec(
        argument_spec={
            "zone_name": {"type": "str", "aliases": ["zone"]},
            "zone_id": {"type": provider_information.get_zone_id_type()},
        },
        required_one_of=[
            ("zone_name", "zone_id"),
        ],
        mutually_exclusive=[
            ("zone_name", "zone_id"),
        ],
    )


@t.overload
def normalize_dns_name(name: str) -> str: ...  # pragma: no cover


@t.overload
def normalize_dns_name(name: str | None) -> str | None: ...  # pragma: no cover


def normalize_dns_name(name: str | None) -> str | None:
    if name is None:
        return name
    labels, dummy = split_into_labels(name)
    return join_labels([normalize_label(label) for label in labels])


def is_prefix(*, normalized_record: str, normalized_zone: str) -> bool:
    return (
        normalized_record.endswith("." + normalized_zone)
        or normalized_record == normalized_zone
    )


def _extract_prefix(*, normalized_record: str, normalized_zone: str) -> str | None:
    # Assumes that is_prefix() returned True
    if normalized_record == normalized_zone:
        return None
    return normalized_record[: len(normalized_record) - len(normalized_zone) - 1]


def get_prefix(
    normalized_zone: str,
    provider_information: ProviderInformation,
    *,
    normalized_record: str | None = None,
    prefix: str | None = None
) -> tuple[str, str | None]:
    # If normalized_record is not specified, use prefix
    if normalized_record is None:
        if prefix is not None:
            prefix = provider_information.normalize_prefix(normalize_dns_name(prefix))
        return (prefix + "." + normalized_zone) if prefix else normalized_zone, prefix
    # Convert record to prefix
    if not is_prefix(
        normalized_record=normalized_record, normalized_zone=normalized_zone
    ):
        raise DNSAPIError("Record must be in zone")
    return (
        normalized_record,
        _extract_prefix(
            normalized_record=normalized_record, normalized_zone=normalized_zone
        ),
    )


def get_zone_id_or_name(
    module_params: dict[str, t.Any], provider_information: ProviderInformation
) -> tuple[str, None] | tuple[None, t.Any] | tuple[str, t.Any]:
    zone_id_name_equal = provider_information.is_zone_id_equal_to_zone_name()
    zone_name: str | None = module_params["zone_name"]
    zone_id: t.Any | None = None if zone_id_name_equal else module_params["zone_id"]
    if zone_name is not None:
        zone_name = normalize_dns_name(zone_name)
    if zone_id is None:
        assert zone_name is not None
        if zone_id_name_equal:
            return zone_name, zone_name
        return zone_name, None
    return None, zone_id


def get_zone_id_or_name_with_prefix_filter(
    module_params: dict[str, t.Any],
    provider_information: ProviderInformation,
    *,
    use_prefix_or_record: bool = False
) -> tuple[str | None, t.Any | None, str | None | NotProvidedType]:
    zone_name, zone_id = get_zone_id_or_name(module_params, provider_information)
    prefix_filter: str | None | NotProvidedType = NOT_PROVIDED
    if use_prefix_or_record:
        prefix = module_params["prefix"]
        record = module_params["record"]
        if prefix is not None:
            prefix_filter = provider_information.normalize_prefix(
                normalize_dns_name(prefix)
            )
        elif record is not None and zone_name is not None:
            normalized_record = normalize_dns_name(record)
            if is_prefix(
                normalized_record=normalized_record, normalized_zone=zone_name
            ):
                prefix_filter = _extract_prefix(
                    normalized_record=normalized_record, normalized_zone=zone_name
                )
    return zone_name, zone_id, prefix_filter
