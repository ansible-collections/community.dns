# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import absolute_import, division, print_function

__metaclass__ = type


import traceback
from collections import OrderedDict, defaultdict

from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
    ModuleOptionProvider,
)
from ansible_collections.community.dns.plugins.module_utils.conversion.base import (
    DNSConversionError,
)
from ansible_collections.community.dns.plugins.module_utils.conversion.converter import (
    RecordConverter,
)
from ansible_collections.community.dns.plugins.module_utils.options import (
    create_bulk_operations_argspec,
    create_record_transformation_argspec,
)
from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_records_for_output,
    format_ttl,
)
from ansible_collections.community.dns.plugins.module_utils.record_set import (
    DNSRecordSet,
    format_record_set_for_output,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIAuthenticationError,
    DNSAPIError,
    ZoneRecordAPI,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_helpers import (
    bulk_apply_changes,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_set_helpers import (
    bulk_apply_changes as rrset_bulk_apply_changes,
)

from ._utils import get_prefix, normalize_dns_name


def create_module_argument_spec(provider_information):
    return ArgumentSpec(
        argument_spec={
            'zone_name': {'type': 'str', 'aliases': ['zone']},
            'zone_id': {'type': provider_information.get_zone_id_type()},
            'prune': {'type': 'bool', 'default': False},
            'record_sets': {
                'type': 'list',
                'elements': 'dict',
                'required': True,
                'aliases': ['records'],
                'options': {
                    'record': {'type': 'str'},
                    'prefix': {'type': 'str'},
                    'ttl': {'type': 'int', 'default': provider_information.get_record_default_ttl()},
                    'type': {'choices': provider_information.get_supported_record_types(), 'required': True},
                    'value': {'type': 'list', 'elements': 'str'},
                    'ignore': {'type': 'bool', 'default': False},
                },
                'required_if': [('ignore', False, ['value'])],
                'required_one_of': [('record', 'prefix')],
                'mutually_exclusive': [('record', 'prefix')],
            },
        },
        required_one_of=[
            ('zone_name', 'zone_id'),
        ],
        mutually_exclusive=[
            ('zone_name', 'zone_id'),
        ],
    ).merge(create_bulk_operations_argspec(provider_information)).merge(create_record_transformation_argspec())


def _get_record_sets_dict(module, provider_information, record_converter, zone_in):
    record_sets = module.params['record_sets']
    record_sets_dict = OrderedDict()
    for index, record_set in enumerate(record_sets):
        record_set = record_set.copy()
        record_name = record_set['record']
        prefix = record_set['prefix']
        record_name, prefix = get_prefix(
            normalized_zone=zone_in, normalized_record=record_name, prefix=prefix, provider_information=provider_information)
        record_set['record'] = record_name
        record_set['prefix'] = prefix
        if record_set['value']:
            record_set['value'] = record_converter.process_values_from_user(record_set['type'], record_set['value'])
        if record_set['type'] not in provider_information.get_supported_record_types():
            module.fail_json(msg='Found invalid record type {type} at index #{i}'.format(type=record_set['type'], i=index))
        key = (prefix, record_set['type'])
        if key in record_sets_dict:
            module.fail_json(msg='Found multiple sets for record {record} and type {type}: index #{i1} and #{i2}'.format(
                record=record_name,
                type=record_set['type'],
                i1=record_sets_dict[key][0],
                i2=index,
            ))
        record_sets_dict[key] = (index, record_set)
    result = OrderedDict()
    for k, (dummy, v) in record_sets_dict.items():
        result[k] = v
    return result


def _run_module_record_api(option_provider, module, provider_information, record_converter, api):
    # Get zone information
    if module.params['zone_name'] is not None:
        zone_in = normalize_dns_name(module.params['zone_name'])
        zone = api.get_zone_with_records_by_name(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_id = zone.zone.id
        zone_records = zone.records
    else:
        zone = api.get_zone_with_records_by_id(module.params['zone_id'])
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_in = normalize_dns_name(zone.zone.name)
        zone_id = zone.zone.id
        zone_records = zone.records

    record_converter.process_multiple_from_api(zone_records)

    # Process parameters
    prune = module.params['prune']
    record_sets_dict = _get_record_sets_dict(module, provider_information, record_converter, zone_in)

    # Group existing record sets
    existing_record_sets = {}
    for record in zone_records:
        key = (record.prefix, record.type)
        if key not in existing_record_sets:
            existing_record_sets[key] = []
        existing_record_sets[key].append(record)

    # Data required for diff
    old_record_sets = {k: [r.clone() for r in v] for k, v in existing_record_sets.items()}
    new_record_sets = {k: list(v) for k, v in existing_record_sets.items()}

    # Create action lists
    to_create = []
    to_delete = []
    to_change = []
    for (prefix, record_type), record_set in record_sets_dict.items():
        key = (prefix, record_type)
        if key not in new_record_sets:
            new_record_sets[key] = []
        existing_recs = existing_record_sets.get(key, [])
        existing_record_sets[key] = []
        new_recs = new_record_sets[key]

        if record_set['ignore']:
            continue

        mismatch_recs = []
        keep_record_sets = []
        values = list(record_set['value'])
        for record in existing_recs:
            if record.ttl != record_set['ttl']:
                mismatch_recs.append(record)
                new_recs.remove(record)
                continue
            if record.target in values:
                values.remove(record.target)
                keep_record_sets.append(record)
            else:
                mismatch_recs.append(record)
                new_recs.remove(record)

        for target in values:
            if mismatch_recs:
                record = mismatch_recs.pop()
                to_change.append(record)
            else:
                # Otherwise create new record
                record = DNSRecord()
                to_create.append(record)
            record.prefix = prefix
            record.type = record_type
            record.ttl = record_set['ttl']
            record.target = target
            new_recs.append(record)

        to_delete.extend(mismatch_recs)

    # If pruning, remove superfluous record sets
    if prune:
        for key, record_set in existing_record_sets.items():
            to_delete.extend(record_set)
            for record in record_set:
                new_record_sets[key].remove(record)

    # Compose result
    result = {
        'changed': False,
        'zone_id': zone_id,
    }

    # Apply changes
    if to_create or to_delete or to_change:
        records_to_delete = record_converter.clone_multiple_to_api(to_delete)
        records_to_change = record_converter.clone_multiple_to_api(to_change)
        records_to_create = record_converter.clone_multiple_to_api(to_create)
        result['changed'] = True
        if not module.check_mode:
            dummy, errors, dummy2 = bulk_apply_changes(
                api,
                zone_id=zone_id,
                records_to_delete=records_to_delete,
                records_to_change=records_to_change,
                records_to_create=records_to_create,
                provider_information=provider_information,
                options=option_provider,
            )
            if errors:
                if len(errors) == 1:
                    raise errors[0]
                module.fail_json(
                    msg='Errors: {0}'.format('; '.join([str(e) for e in errors])),
                    errors=[str(e) for e in errors],
                )

    # Include diff information
    if module._diff:
        def sort_items(dictionary):
            items = [
                (zone_in if prefix is None else (prefix + '.' + zone_in), record_type, prefix, record_set)
                for (prefix, record_type), record_set in dictionary.items() if len(record_set) > 0
            ]
            return sorted(items)

        result['diff'] = {
            'before': {
                'record_sets': [
                    format_records_for_output(record_set, record_name, prefix, record_converter=record_converter)
                    for record_name, record_type, prefix, record_set in sort_items(old_record_sets)
                ],
            },
            'after': {
                'record_sets': [
                    format_records_for_output(record_set, record_name, prefix, record_converter=record_converter)
                    for record_name, record_type, prefix, record_set in sort_items(new_record_sets)
                ],
            },
        }

    module.exit_json(**result)


def _run_module_record_set_api(option_provider, module, provider_information, record_converter, api):
    # Get zone information
    if module.params['zone_name'] is not None:
        zone_in = normalize_dns_name(module.params['zone_name'])
        zone = api.get_zone_with_record_sets_by_name(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_id = zone.zone.id
        zone_record_sets = zone.record_sets
    else:
        zone = api.get_zone_with_record_sets_by_id(module.params['zone_id'])
        if zone is None:
            module.fail_json(msg='Zone not found')
        zone_in = normalize_dns_name(zone.zone.name)
        zone_id = zone.zone.id
        zone_record_sets = zone.record_sets

    for record_set in zone_record_sets:
        record_converter.process_set_from_api(record_set)

    # Process parameters
    prune = module.params['prune']
    record_sets_dict = _get_record_sets_dict(module, provider_information, record_converter, zone_in)

    # Group existing record sets
    existing_record_sets = OrderedDict()
    for record_set in zone_record_sets:
        key = (record_set.prefix, record_set.type)
        existing_record_sets[key] = record_set

    # Data required for diff
    old_record_sets = {k: v.clone() for k, v in existing_record_sets.items()}
    new_record_sets = dict(existing_record_sets)

    # Create action lists
    to_create = []
    to_delete = []
    to_change = []
    for (prefix, record_type), record_set in record_sets_dict.items():
        key = (prefix, record_type)
        existing_record_sets.pop(key, None)
        if record_set['ignore']:
            continue

        new_rrset = new_record_sets.get(key)

        ttl = record_set['ttl']
        values = sorted(record_set['value'])
        if not values:
            if new_rrset:
                to_delete.append(new_rrset)
                new_record_sets.pop(key)
            continue

        if new_rrset is None:
            rrset = DNSRecordSet()
            rrset.prefix = prefix
            rrset.type = record_type
            rrset.ttl = ttl
            rrset.records = []
            for value in values:
                rec = DNSRecord()
                rec.prefix = prefix
                rec.type = record_type
                rec.ttl = ttl
                rec.target = value
                rrset.records.append(rec)
            to_create.append(rrset)
            new_record_sets[key] = rrset
            continue

        mismatch_ttl = ttl != new_rrset.ttl
        mismatch_values = values != sorted((rec.target for rec in new_rrset.records))
        if not mismatch_ttl and not mismatch_values:
            continue

        to_change.append((new_rrset, mismatch_values, mismatch_ttl))
        existing_records = defaultdict(list)
        for rec in new_rrset.records:
            existing_records[rec.target].append(rec)

        new_rrset.records[:] = []
        new_rrset.ttl = ttl
        for value in values:
            recs = existing_records.get(value)
            if recs:
                new_rrset.records.append(recs.pop())
                continue
            rec = DNSRecord()
            rec.prefix = prefix
            rec.type = record_type
            rec.target = value
            new_rrset.records.append(rec)

    # If pruning, remove superfluous record sets
    if prune:
        for key, record_set in existing_record_sets.items():
            to_delete.append(record_set)
            new_record_sets.pop(key)

    # Compose result
    result = {
        'changed': False,
        'zone_id': zone_id,
    }

    def _get_name(prefix):
        return zone_in if prefix is None else (prefix + '.' + zone_in)

    # Apply changes
    if to_create or to_delete or to_change:
        record_sets_to_delete = [record_converter.clone_set_to_api(rrset) for rrset in to_delete]
        record_sets_to_change = [
            (record_converter.clone_set_to_api(rrset), mismatch_values, mismatch_ttl)
            for rrset, mismatch_values, mismatch_ttl in to_change
        ]
        record_sets_to_create = [record_converter.clone_set_to_api(rrset) for rrset in to_create]
        result['changed'] = True
        if not module.check_mode:
            dummy, errors, dummy2 = rrset_bulk_apply_changes(
                api,
                zone_id=zone_id,
                record_sets_to_delete=record_sets_to_delete,
                record_sets_to_change=record_sets_to_change,
                record_sets_to_create=record_sets_to_create,
                provider_information=provider_information,
                options=option_provider,
            )
            if errors:
                messages = [
                    "{0} record set {2} {1} with TTL={3} and value={4}: {5}".format(
                        what.title(),
                        _get_name(record_set.prefix),
                        record_set.type,
                        format_ttl(record_set.ttl),
                        record_converter.process_values_to_user(record_set.type, [rec.target for rec in record_set.records]),
                        e,
                    )
                    for what, record_set, e in errors
                ]
                module.fail_json(
                    msg='Errors: {0}'.format('; '.join(messages)),
                    errors=[str(e) for dummy, dummy2, e in errors],
                )

    # Include diff information
    if module._diff:
        def sort_items(dictionary):
            items = [
                (_get_name(prefix), record_type, prefix, record_set)
                for (prefix, record_type), record_set in dictionary.items()
            ]
            return sorted(items)

        result['diff'] = {
            'before': {
                'record_sets': [
                    format_record_set_for_output(record_set, record_name, prefix, record_converter=record_converter)
                    for record_name, record_type, prefix, record_set in sort_items(old_record_sets)
                ],
            },
            'after': {
                'record_sets': [
                    format_record_set_for_output(record_set, record_name, prefix, record_converter=record_converter)
                    for record_name, record_type, prefix, record_set in sort_items(new_record_sets)
                ],
            },
        }

    module.exit_json(**result)


def run_module(module, create_api, provider_information):
    option_provider = ModuleOptionProvider(module)
    record_converter = RecordConverter(provider_information, option_provider)
    record_converter.emit_deprecations(module.deprecate)

    try:
        # Create API
        api = create_api()

        if isinstance(api, ZoneRecordAPI):
            _run_module_record_api(option_provider, module, provider_information, record_converter, api)
        else:
            _run_module_record_set_api(option_provider, module, provider_information, record_converter, api)

    except DNSConversionError as e:
        module.fail_json(msg='Error while converting DNS values: {0}'.format(e.error_message), error=e.error_message, exception=traceback.format_exc())
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=to_text(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=to_text(e), exception=traceback.format_exc())
