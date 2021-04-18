# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This module_utils is PRIVATE and should only be used by this collection. Breaking changes can occur any time.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


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
)

from ._utils import (
    normalize_dns_name,
    get_prefix,
)


def create_module_argument_spec():
    return ArgumentSpec(
        argument_spec=dict(
            state=dict(type='str', choices=['present', 'absent'], required=True),
            zone=dict(type='str', required=True),
            record=dict(type='str', required=True),
            ttl=dict(type='int', default=3600),
            type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], required=True),
            value=dict(required=True, type='list', elements='str'),
            overwrite=dict(default=False, type='bool'),
        ),
    )


def run_module(module, create_api):
    # Get zone and record
    zone_in = normalize_dns_name(module.params.get('zone'))
    record_in = normalize_dns_name(module.params.get('record'))

    try:
        # Convert record to prefix
        prefix, dummy = get_prefix(record_in, zone_in)
        # Create API
        api = create_api()
        # Get zone information
        zone = api.get_zone_with_records_by_name(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e))
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e))

    # Find matching records
    type_in = module.params.get('type')
    records = []
    for record in zone.records:
        if record.prefix == prefix and record.type == type_in:
            records.append(record)

    # Parse records
    values = []
    value_in = module.params.get('value')
    values = value_in[:]

    # Compare records
    ttl_in = module.params.get('ttl')
    mismatch = False
    mismatch_records = []
    keep_records = []
    for record in records:
        if record.ttl != ttl_in:
            mismatch = True
            mismatch_records.append(record)
            continue
        val = record.target
        if val in values:
            values.remove(val)
            keep_records.append(record)
        else:
            mismatch = True
            mismatch_records.append(record)
            continue
    if values:
        mismatch = True

    before = [record.clone() for record in records]
    after = keep_records[:]

    # Determine what to do
    to_create = []
    to_delete = []
    to_change = []
    if module.params.get('state') == 'present':
        if records and mismatch:
            # Mismatch: user wants to overwrite?
            if module.params.get('overwrite'):
                to_delete.extend(mismatch_records)
            else:
                module.fail_json(msg="Record already exists with different value. Set 'overwrite' to replace it")
        for target in values:
            if to_delete:
                # If there's a record to delete, change it to new record
                record = to_delete.pop()
                to_change.append(record)
            else:
                # Otherwise create new record
                record = DNSRecord()
                to_create.append(record)
            record.prefix = prefix
            record.type = type_in
            record.ttl = ttl_in
            record.target = target
            after.append(record)
    if module.params.get('state') == 'absent':
        if not mismatch:
            to_delete.extend(records)
            after = []

    # Is there nothing to change?
    if len(to_create) == 0 and len(to_delete) == 0 and len(to_change) == 0:
        module.exit_json(changed=False)

    # Actually do something
    if not module.check_mode:
        try:
            for record in to_delete:
                api.delete_record(zone.zone.id, record)
            for record in to_change:
                api.update_record(zone.zone.id, record)
            for record in to_create:
                api.add_record(zone.zone.id, record)
        except DNSAPIAuthenticationError as e:
            module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e))
        except DNSAPIError as e:
            module.fail_json(msg='Error: {0}'.format(e), error=str(e))

    result = dict(changed=True)
    if module._diff:
        result['diff'] = dict(
            before=format_records_for_output(sorted(before, key=lambda record: record.target), record_in) if before else dict(),
            after=format_records_for_output(sorted(after, key=lambda record: record.target), record_in) if after else dict(),
        )

    module.exit_json(**result)
