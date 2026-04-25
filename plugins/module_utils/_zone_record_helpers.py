# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    DNSAPIError,
)

if t.TYPE_CHECKING:
    from collections.abc import Sequence  # pragma: no cover

    from ._argspec import OptionProvider  # pragma: no cover
    from ._provider import ProviderInformation  # pragma: no cover
    from ._record import DNSRecord, IDNSRecord, RecordIDT  # pragma: no cover
    from ._zone import ZoneIDT  # pragma: no cover
    from ._zone_record_api import ZoneRecordAPI  # pragma: no cover

    class _Result(t.TypedDict, t.Generic[RecordIDT]):  # pragma: no cover
        deleted: list[DNSRecord[RecordIDT]]  # pragma: no cover
        changed: list[DNSRecord[RecordIDT]]  # pragma: no cover
        created: list[DNSRecord[RecordIDT]]  # pragma: no cover


def bulk_apply_changes(
    api: ZoneRecordAPI[ZoneIDT, RecordIDT],
    provider_information: ProviderInformation,
    options: OptionProvider,
    zone_id: ZoneIDT,
    records_to_delete: Sequence[DNSRecord[RecordIDT]] | None = None,
    records_to_change: Sequence[DNSRecord[RecordIDT]] | None = None,
    records_to_create: Sequence[IDNSRecord[RecordIDT | None]] | None = None,
    stop_early_on_errors: bool = True,
) -> tuple[bool, list[DNSAPIError], _Result[RecordIDT]]:
    """
    Update multiple records. If an operation failed, raise a DNSAPIException.

    @param api: A ZoneRecordAPI instance
    @param provider_information: A ProviderInformation object.
    @param options: A object compatible with ModuleOptionProvider that gives access to the module/plugin
                    options.
    @param zone_id: Zone ID to apply changes to
    @param records_to_delete: Optional list of DNS records to delete (DNSRecord)
    @param records_to_change: Optional list of DNS records to change (DNSRecord)
    @param records_to_create: Optional list of DNS records to create (DNSRecord)
    @param bulk_threshold: Minimum number of changes for using the bulk API instead of the regular API
    @param stop_early_on_errors: If set to ``True``, try to stop changes after the first error happens.
                                 This might only work on some APIs.
    @return A tuple (changed, errors, success) where ``changed`` is a boolean which indicates whether a
            change was made, ``errors`` is a list of ``DNSAPIError`` instances for the errors occurred,
            and ``success`` is a dictionary with three lists ``success['deleted']``,
            ``success['changed']`` and ``success['created']``, which list all records that were deleted,
            changed and created, respectively.
    """
    records_to_delete = records_to_delete or []
    records_to_change = records_to_change or []
    records_to_create = records_to_create or []

    has_change = False
    errors: list[DNSAPIError] = []

    bulk_threshold = 2
    if provider_information.supports_bulk_actions():
        bulk_threshold = options.get_option("bulk_operation_threshold")

    success: _Result[RecordIDT] = {
        "deleted": [],
        "changed": [],
        "created": [],
    }

    # Delete records
    if len(records_to_delete) >= bulk_threshold:
        results = api.delete_records(
            {zone_id: records_to_delete}, stop_early_on_errors=stop_early_on_errors
        )
        result = results.get(zone_id) or []
        for record, deleted, failed in result:
            has_change |= deleted
            if failed is not None:
                errors.append(failed)
            if deleted:
                success["deleted"].append(record)
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for record in records_to_delete:
            try:
                deleted = api.delete_record(zone_id, record)
                has_change |= deleted
                if deleted:
                    success["deleted"].append(record)
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors, success

    # Change records
    if len(records_to_change) >= bulk_threshold:
        results = api.update_records(
            {zone_id: records_to_change}, stop_early_on_errors=stop_early_on_errors
        )
        result = results.get(zone_id) or []
        for record, changed, failed in result:
            has_change |= changed
            if failed is not None:
                errors.append(failed)
            if changed:
                success["changed"].append(record)
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for record in records_to_change:
            try:
                record = api.update_record(zone_id, record)
                has_change = True
                success["changed"].append(record)
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors, success

    # Create records
    if len(records_to_create) >= bulk_threshold:
        create_results = api.add_records(
            {zone_id: records_to_create}, stop_early_on_errors=stop_early_on_errors
        )
        create_result = create_results.get(zone_id) or []
        for crecord, created, failed in create_result:
            has_change |= created
            if failed is not None:
                errors.append(failed)
            if created:
                success["created"].append(crecord)  # type: ignore  # if created is True, crecord is a DNSRecord
        if errors and stop_early_on_errors:
            return has_change, errors, success
    else:
        for create_record in records_to_create:
            try:
                created_record = api.add_record(zone_id, create_record)
                has_change = True
                success["created"].append(created_record)
            except DNSAPIError as e:
                errors.append(e)
                if stop_early_on_errors:
                    return has_change, errors, success

    return has_change, errors, success
