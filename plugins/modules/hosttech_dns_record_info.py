#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hosttech_dns_record_info

short_description: Retrieve entries in Hosttech DNS service

version_added: 0.1.0

description:
    - "Retrieves DNS records in Hosttech DNS service U(https://ns1.hosttech.eu/public/api?wsdl)."

notes:
    - "Supports C(check_mode)."

options:
    what:
        description:
        - Describes whether to fetch a single record and type combination, all types for a
          record, or all records. By default, a single record and type combination is fetched.
        - Note that the return value structure depends on this option.
        choices: ['single_record', 'all_types_for_record', 'all_records']
        default: single_record
        type: str
    zone:
        description:
        - The DNS zone to modify.
        required: yes
        type: str
    record:
        description:
        - The full DNS record to retrieve.
        - Required if I(what) is C(single_record) or C(all_types_for_record).
        type: str
    type:
        description:
        - The type of DNS record to retrieve.
        - Required if I(what) is C(single_record).
        choices: ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
        type: str

extends_documentation_fragment:
    - community.dns.hosttech

author:
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Retrieve the details for new.foo.com
  community.dns.hosttech_dns_record_info:
    zone: foo.com
    record: new.foo.com
    type: A
    hosttech_username: foo
    hosttech_password: bar
  register: rec

- name: Delete new.foo.com A record using the results from the above command
  community.dns.hosttech_dns_record:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"
    hosttech_username: foo
    hosttech_password: bar
'''

RETURN = '''
set:
    description: The fetched record. Is empty if record does not exist.
    type: dict
    returned: success and I(what) is C(single_record)
    contains:
        record:
            description: The record name.
            type: str
            sample: sample.example.com
        type:
            description: The DNS record type.
            type: str
            sample: A
        ttl:
            description: The TTL.
            type: int
            sample: 3600
        value:
            description: The DNS record.
            type: list
            elements: str
            sample:
            - 1.2.3.4
            - 1.2.3.5
    sample:
        record: sample.example.com
        type: A
        ttl: 3600
        value:
        - 1.2.3.4
        - 1.2.3.5
sets:
    description: The list of fetched records.
    type: list
    elements: dict
    returned: success and I(what) is not C(single_record)
    contains:
        record:
            description: The record name.
            type: str
            sample: sample.example.com
        type:
            description: The DNS record type.
            type: str
            sample: A
        ttl:
            description: The TTL.
            type: int
            sample: 3600
        value:
            description: The DNS record.
            type: list
            elements: str
            sample:
            - 1.2.3.4
            - 1.2.3.5
    sample:
        - record: sample.example.com
          type: A
          ttl: 3600
          value:
          - 1.2.3.4
          - 1.2.3.5
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.wsdl import (
    HAS_LXML_ETREE, WSDLException, WSDLNetworkError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.errors import (
    HostTechAPIError, HostTechAPIAuthError,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.record import (
    format_records_for_output,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.wsdl_api import (
    HostTechWSDLAPI,
)


def get_prefix(module, zone_in):
    # Get zone and record.
    record_in = module.params.get('record').lower()
    if record_in[-1:] == '.':
        record_in = record_in[:-1]

    # Convert record to prefix
    if not record_in.endswith('.' + zone_in) and record_in != zone_in:
        module.fail_json(msg='Record must be in zone')
    if record_in == zone_in:
        return None, record_in
    else:
        return record_in[:len(record_in) - len(zone_in) - 1], record_in


def run_module():
    module_args = dict(
        what=dict(type='str', choices=['single_record', 'all_types_for_record', 'all_records'], default='single_record'),
        zone=dict(type='str', required=True),
        record=dict(type='str', default=None),
        type=dict(type='str', choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], default=None),
        hosttech_username=dict(type='str', required=True),
        hosttech_password=dict(type='str', required=True, no_log=True),
    )
    required_if = [
        ('what', 'single_record', ['record', 'type']),
        ('what', 'all_types_for_record', ['record']),
    ]
    module = AnsibleModule(argument_spec=module_args, required_if=required_if, supports_check_mode=True)

    if not HAS_LXML_ETREE:
        module.fail_json(msg='Needs lxml Python module (pip install lxml)')

    # Get zone and record.
    zone_in = module.params.get('zone').lower()
    if zone_in[-1:] == '.':
        zone_in = zone_in[:-1]

    # Create API and get zone information
    api = HostTechWSDLAPI(module.params.get('hosttech_username'), module.params.get('hosttech_password'), debug=False)
    try:
        zone = api.get_zone(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
    except HostTechAPIAuthError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), exception=e)
    except HostTechAPIError as e:
        module.fail_json(msg='Internal error (API level): {0}'.format(e), exception=e)
    except WSDLNetworkError as e:
        module.fail_json(msg='Network error: {0}'.format(e), exception=e)
    except WSDLException as e:
        module.fail_json(msg='Internal error (WSDL level): {0}'.format(e), exception=e)

    if module.params.get('what') == 'single_record':
        # Extract prefix
        prefix, record_in = get_prefix(module, zone_in)

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
        )
    else:
        # Extract prefix if necessary
        if module.params.get('what') == 'all_types_for_record':
            check_prefix = True
            prefix, dummy = get_prefix(module, zone_in)
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
        )


def main():
    run_module()


if __name__ == '__main__':
    main()
