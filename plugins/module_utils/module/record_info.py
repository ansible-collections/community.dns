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


def create_module_argument_spec(zone_id_type='str'):
    return ArgumentSpec(
        argument_spec=dict(
            what=dict(type='str', choices=['single_record', 'all_types_for_record', 'all_records'], default='single_record'),
            zone=dict(type='str'),
            zone_id=dict(type=zone_id_type),
            record=dict(type='str', default=None),
            type=dict(type='str', choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], default=None),
        ),
        required_if=[
            ('what', 'single_record', ['record', 'type']),
            ('what', 'all_types_for_record', ['record']),
        ],
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
        if module.params.get('zone') is not None:
            zone_in = normalize_dns_name(module.params.get('zone'))
            zone = api.get_zone_with_records_by_name(zone_in)
            if zone is None:
                module.fail_json(msg='Zone not found')
        else:
            zone = api.get_zone_with_records_by_id(module.params.get('zone_id'))
            if zone is None:
                module.fail_json(msg='Zone not found')
            zone_in = normalize_dns_name(zone.zone.name)

        # Retrieve requested information
        if module.params.get('what') == 'single_record':
            # Extract prefix
            record_in = normalize_dns_name(module.params.get('record'))
            prefix = get_prefix(record_in, zone_in)

            # Find matching records
            type_in = module.params.get('type')
            records = []
            for record in zone.records:
                if record.prefix == prefix and record.type == type_in:
                    records.append(record)

            # Format output
            data = format_records_for_output(records, record_in) if records else {}
            module.exit_json(
                changed=False,
                set=data,
                zone_id=zone.zone.id,
            )
        else:
            # Extract prefix if necessary
            if module.params.get('what') == 'all_types_for_record':
                check_prefix = True
                prefix = get_prefix(normalize_dns_name(module.params.get('record')), zone_in)
            else:
                check_prefix = False
                prefix = None

            # Find matching records
            records = {}
            for record in zone.records:
                if check_prefix:
                    if record.prefix != prefix:
                        continue
                key = ((record.prefix + '.' + zone_in) if record.prefix else zone_in, record.type)
                record_list = records.get(key)
                if record_list is None:
                    record_list = records[key] = []
                record_list.append(record)

            # Format output
            data = [format_records_for_output(record_list, record_name) for (record_name, dummy), record_list in sorted(records.items())]
            module.exit_json(
                changed=False,
                sets=data,
                zone_id=zone.zone.id,
            )
    except DNSAPIAuthenticationError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e), exception=traceback.format_exc())
    except DNSAPIError as e:
        module.fail_json(msg='Error: {0}'.format(e), error=str(e), exception=traceback.format_exc())
