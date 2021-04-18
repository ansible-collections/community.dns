#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hosttech_dns_record

short_description: Add or delete entries in Hosttech DNS service

version_added: 0.1.0

description:
    - "Creates and deletes DNS records in Hosttech DNS service U(https://ns1.hosttech.eu/public/api?wsdl)."

notes:
    - "Supports C(check_mode) and C(--diff)."

options:
    state:
        description:
        - Specifies the state of the resource record.
        required: true
        choices: ['present', 'absent']
        type: str
    zone:
        description:
        - The DNS zone to modify.
        required: true
        type: str
    record:
        description:
        - The full DNS record to create or delete.
        required: true
        type: str
    ttl:
        description:
        - The TTL to give the new record, in seconds.
        default: 3600
        type: int
    type:
        description:
        - The type of DNS record to create or delete.
        required: true
        choices: ['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA']
        type: str
    value:
        description:
        - The new value when creating a DNS record.
        - YAML lists or multiple comma-spaced values are allowed.
        - When deleting a record all values for the record must be specified or it will
          not be deleted.
        required: true
        type: list
        elements: str
    overwrite:
        description:
        - Whether an existing record should be overwritten on create if values do not
          match.
        default: false
        type: bool

extends_documentation_fragment:
    - community.dns.hosttech

author:
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Add new.foo.com as an A record with 3 IPs
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value: 1.1.1.1,2.2.2.2,3.3.3.3
    hosttech_username: foo
    hosttech_password: bar

- name: Update new.foo.com as an A record with a list of 3 IPs
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: new.foo.com
    type: A
    ttl: 7200
    value:
      - 1.1.1.1
      - 2.2.2.2
      - 3.3.3.3
    hosttech_username: foo
    hosttech_password: bar

- name: Retrieve the details for new.foo.com
  community.dns.hosttech_dns_record_info:
    zone: foo.com
    record: new.foo.com
    type: A
    hosttech_username: foo
    hosttech_password: bar
  register: rec

- name: Delete new.foo.com A record using the results from the facts retrieval command
  community.dns.hosttech_dns_record:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"
    hosttech_username: foo
    hosttech_password: bar

- name: Add an AAAA record
  # Note that because there are colons in the value that the IPv6 address must be quoted!
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: localhost.foo.com
    type: AAAA
    ttl: 7200
    value: "::1"
    hosttech_username: foo
    hosttech_password: bar

- name: Add a TXT record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: localhost.foo.com
    type: TXT
    ttl: 7200
    value: 'bar'
    hosttech_username: foo
    hosttech_password: bar

- name: Remove the TXT record
  community.dns.hosttech_dns_record:
    state: absent
    zone: foo.com
    record: localhost.foo.com
    type: TXT
    ttl: 7200
    value: 'bar'
    hosttech_username: foo
    hosttech_password: bar

- name: Add a CAA record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: CAA
    ttl: 3600
    value:
    - "128 issue letsencrypt.org"
    - "128 iodef mailto:webmaster@foo.com"
    hosttech_username: foo
    hosttech_password: bar

- name: Add an MX record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: MX
    ttl: 3600
    value:
    - "10 mail.foo.com"
    hosttech_username: foo
    hosttech_password: bar

- name: Add a CNAME record
  community.dns.hosttech_dns_record:
    state: present
    zone: bla.foo.com
    record: foo.com
    type: CNAME
    ttl: 3600
    value:
    - foo.foo.com
    hosttech_username: foo
    hosttech_password: bar

- name: Add a PTR record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.foo.com
    record: foo.com
    type: PTR
    ttl: 3600
    value:
    - foo.foo.com
    hosttech_username: foo
    hosttech_password: bar

- name: Add an SPF record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: SPF
    ttl: 3600
    value:
    - "v=spf1 a mx ~all"
    hosttech_username: foo
    hosttech_password: bar

- name: Add a PTR record
  community.dns.hosttech_dns_record:
    state: present
    zone: foo.com
    record: foo.com
    type: PTR
    ttl: 3600
    value:
    - "10 100 3333 service.foo.com"
    hosttech_username: foo
    hosttech_password: bar
'''

RETURN = ''' # '''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.record import (
    DNSRecord,
    format_records_for_output,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    create_argument_spec,
    create_api,
)

from ansible_collections.community.dns.plugins.module_utils.hosttech.errors import (
    HostTechAPIError,
    HostTechAPIAuthError,
)


def run_module():
    argument_spec = create_argument_spec()
    argument_spec['argument_spec'].update(dict(
        state=dict(type='str', choices=['present', 'absent'], required=True),
        zone=dict(type='str', required=True),
        record=dict(type='str', required=True),
        ttl=dict(type='int', default=3600),
        type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'NS', 'CAA'], required=True),
        value=dict(required=True, type='list', elements='str'),
        overwrite=dict(default=False, type='bool'),
    ))
    module = AnsibleModule(supports_check_mode=True, **argument_spec)

    # Create API
    api = create_api(module)

    # Get zone and record.
    zone_in = module.params.get('zone').lower()
    record_in = module.params.get('record').lower()
    if zone_in[-1:] == '.':
        zone_in = zone_in[:-1]
    if record_in[-1:] == '.':
        record_in = record_in[:-1]

    # Convert record to prefix
    if not record_in.endswith('.' + zone_in) and record_in != zone_in:
        module.fail_json(msg='Record must be in zone')
    if record_in == zone_in:
        prefix = None
    else:
        prefix = record_in[:len(record_in) - len(zone_in) - 1]

    # Get zone information
    try:
        zone = api.get_zone_with_records_by_name(zone_in)
        if zone is None:
            module.fail_json(msg='Zone not found')
    except HostTechAPIAuthError as e:
        module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e))
    except HostTechAPIError as e:
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
        except HostTechAPIAuthError as e:
            module.fail_json(msg='Cannot authenticate: {0}'.format(e), error=str(e))
        except HostTechAPIError as e:
            module.fail_json(msg='Error: {0}'.format(e), error=str(e))

    result = dict(changed=True)
    if module._diff:
        result['diff'] = dict(
            before=format_records_for_output(sorted(before, key=lambda record: record.target), record_in) if before else dict(),
            after=format_records_for_output(sorted(after, key=lambda record: record.target), record_in) if after else dict(),
        )

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
