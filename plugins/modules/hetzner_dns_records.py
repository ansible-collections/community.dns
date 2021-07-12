#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hetzner_dns_records

short_description: Bulk synchronize DNS records in Hetzner DNS service

version_added: 2.0.0

description:
    - Bulk synchronize DNS records in Hetzner DNS service.

extends_documentation_fragment:
    - community.dns.hetzner
    - community.dns.module_records

options:
    zone_id:
        type: str
    records:
        suboptions:
            type:
                choices: ['A', 'AAAA', 'NS', 'MX', 'CNAME', 'RP', 'TXT', 'SOA', 'HINFO', 'SRV', 'DANE', 'TLSA', 'DS', 'CAA']
        # The following madness is needed because of the primitive merging of docs fragments:
                description:
                  - The type of DNS record to create or delete.
                required: true
                type: str
            record:
                description:
                  - The full DNS record to create or delete.
                  - Exactly one of I(record) and I(prefix) must be specified.
                type: str
            prefix:
                description:
                  - The prefix of the DNS record.
                  - This is the part of I(record) before I(zone). For example, if the record to be modified is C(www.example.com)
                    for the zone C(example.com), the prefix is C(www). If the record in this example would be C(example.com), the
                    prefix would be C('') (empty string).
                  - Exactly one of I(record) and I(prefix) must be specified.
                type: str
            ttl:
                description:
                  - The TTL to give the new record, in seconds.
                default: 3600
                type: int
            value:
                description:
                  - The new value when creating a DNS record.
                  - YAML lists or multiple comma-spaced values are allowed.
                  - When deleting a record all values for the record must be specified or it will
                    not be deleted.
                  - Must be specified if I(ignore=false).
                type: list
                elements: str
            ignore:
                description:
                  - If set to C(true), I(value) will be ignored.
                  - This is useful when I(prune=true), but you do not want certain entries to be removed
                    without having to know their current value.
                type: bool
                default: false

author:
    - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
    - Felix Fontein (@felixfontein)

'''

EXAMPLES = '''
- name: Make sure some records exist and have the expected values
  community.dns.hetzner_dns_records:
    zone: foo.com
    records:
      - prefix: new
        type: A
        ttl: 7200
        value:
          - 1.1.1.1
          - 2.2.2.2
      - prefix: new
        type: AAAA
        ttl: 7200
        value:
          - "::1"
      - zone: foo.com
        type: TXT
        value:
          - test
    hetzner_token: access_token

- name: Synchronize DNS zone with a fixed set of records
  # If a record exists that is not mentioned here, it will be deleted
  community.dns.hetzner_dns_records:
    zone_id: 23
    purge: true
    records:
      - prefix: ''
        type: A
        value: 127.0.0.1
      - prefix: ''
        type: AAAA
        value: "::1"
      - prefix: ''
        type: NS
        value:
          - ns-1.hoster.com
          - ns-2.hoster.com
          - ns-3.hoster.com
    hetzner_token: access_token
'''

RETURN = '''
zone_id:
    description: The ID of the zone.
    type: str
    returned: success
    sample: 23
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.hetzner.api import (
    create_hetzner_argument_spec,
    create_hetzner_api,
    create_hetzner_provider_information,
)

from ansible_collections.community.dns.plugins.module_utils.module.records import (
    create_module_argument_spec,
    run_module,
)


def main():
    provider_information = create_hetzner_provider_information()
    argument_spec = create_hetzner_argument_spec()
    argument_spec.merge(create_module_argument_spec(zone_id_type='str', provider_information=provider_information))
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hetzner_api(module), provider_information=provider_information)


if __name__ == '__main__':
    main()
