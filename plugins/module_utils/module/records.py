# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


import traceback

from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_records_for_output,
)

from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    DNSAPIError,
    DNSAPIAuthenticationError,
    NOT_PROVIDED,
    filter_records,
)

from ._utils import (
    normalize_dns_name,
    get_prefix,
)


def create_module_argument_spec(zone_id_type='str'):
    return ArgumentSpec(
        argument_spec=dict(
            zone=dict(type='str'),
            zone_id=dict(type=zone_id_type),
            prune=dict(type='bool', default=False),
            records=dict(
                type='list',
                elements='dict',
                required=True,
                options=dict(
                    record=dict(type='str'),
                    prefix=dict(type='str'),
                    ttl=dict(type='int', default=3600),
                    type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], required=True),
                    value=dict(type='list', elements='str'),
                    ignore=dict(type='bool', default=False),
                ),
                required_if=[('ignore', False, ['value'])],
                required_one_of=[('record', 'prefix')],
                mutually_exclusive=[('record', 'prefix')],
            ),
        ),
        required_one_of=[
            ('zone', 'zone_id'),
        ],
        mutually_exclusive=[
            ('zone', 'zone_id'),
        ],
    )


def run_module(module, create_api):
    try:
        # Create API
        api = create_api()

        # Get zone information
        if module.params['zone'] is not None:
            zone_in = normalize_dns_name(module.params['zone'])
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

        # Process parameters
        prune = module.params['prune']
        records = module.params['records']
        records_dict = dict()
        for index, record in enumerate(records):
            record = record.copy()
            record_name = record.pop('record')
            prefix = record['prefix'] or None
            record_name, prefix = get_prefix(normalized_zone=zone_in, normalized_record=record_name, prefix=prefix)
            record['record'] = record_name
            record['prefix'] = prefix
            key = (prefix, record['type'])
            if key in records_dict:
                module.fail_json(msg='Found multiple entries for record {record} and type {type}: index #{i1} and #{i2}'.format(
                    record=record_name,
                    type=record['type'],
                    i1=records_dict[key][0],
                    i2=index,
                ))
            records_dict[key] = (index, record)

        # Group existing records
        existing_records = dict()
        for record in zone_records:
            key = (record.prefix, record.type)
            if key not in existing_records:
                existing_records[key] = []
            existing_records[key].append(record)

        # Data required for diff
        old_records = dict([(k, [r.clone() for r in v]) for k, v in existing_records.items()])
        new_records = dict([(k, list(v)) for k, v in existing_records.items()])

        # Create action lists
        to_create = []
        to_delete = []
        to_change = []
        for (prefix, record_type), (dummy, record_data) in records_dict.items():
            key = (prefix, record_type)
            if key not in new_records:
                new_records[key] = []
            existing_recs = existing_records.get(key, [])
            existing_records[key] = []
            new_recs = new_records[key]

            if record_data['ignore']:
                continue

            mismatch_recs = []
            keep_records = []
            values = list(record_data['value'])
            for record in existing_recs:
                if record.ttl != record_data['ttl']:
                    mismatch_recs.append(record)
                    new_recs.remove(record)
                    continue
                if record.target in values:
                    values.remove(record.target)
                    keep_records.append(record)
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
                record.ttl = record_data['ttl']
                record.target = target
                new_recs.append(record)

            to_delete.extend(mismatch_recs)

        # If pruning, remove superfluous records
        if prune:
            for key, record_list in existing_records.items():
                to_delete.extend(record_list)
                for record in record_list:
                    new_records[key].remove(record)

        # Apply changes
        result = dict(
            changed=False,
            zone_id=zone_id,
        )
        if to_create or to_delete or to_change:
            result['changed'] = True
            if not module.check_mode:
                for record in to_delete:
                    api.delete_record(zone_id, record)
                for record in to_change:
                    api.update_record(zone_id, record)
                for record in to_create:
                    api.add_record(zone_id, record)

        # Include diff information
        if module._diff:
            def sort_items(dictionary):
                items = [
                    (zone_in if prefix is None else (prefix + '.' + zone_in), type, prefix, records)
                    for (prefix, type), records in dictionary.items() if len(records) > 0
                ]
                return sorted(items)

            result['diff'] = dict(
                before=dict(
                    records=[
                        format_records_for_output(record_list, record_name, prefix)
                        for record_name, type, prefix, record_list in sort_items(old_records)
                    ],
                ),
                after=dict(
                    records=[
                        format_records_for_output(record_list, record_name, prefix)
                        for record_name, type, prefix, record_list in sort_items(new_records)
                    ],
                ),
            )

        module.exit_json(**result)
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
