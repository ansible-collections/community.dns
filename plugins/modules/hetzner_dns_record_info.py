#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = '''
---
module: hetzner_dns_record_info

short_description: Retrieve entries in Hetzner DNS service

version_added: 1.2.0

description:
    - "Retrieves DNS records in Hetzner DNS service."

extends_documentation_fragment:
    - community.dns.hetzner
    - community.dns.module_record_info

options:
    zone_id:
        type: str

author:
    - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
    - Felix Fontein (@felixfontein)
'''

EXAMPLES = '''
- name: Retrieve the details for new.foo.com
  community.dns.hetzner_dns_record_info:
    zone: foo.com
    record: new.foo.com
    type: A
    hetzner_token: access_token
  register: rec

- name: Delete new.foo.com A record using the results from the above command
  community.dns.hetzner_dns_record:
    state: absent
    zone: foo.com
    record: "{{ rec.set.record }}"
    ttl: "{{ rec.set.ttl }}"
    type: "{{ rec.set.type }}"
    value: "{{ rec.set.value }}"
    hetzner_token: access_token
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
        prefix:
            description: The record prefix.
            type: str
            sample: sample
            version_added: 0.2.0
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
        prefix:
            description: The record prefix.
            type: str
            sample: sample
            version_added: 0.2.0
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

zone_id:
    description: The ID of the zone.
    type: str
    returned: success
    sample: 23
    version_added: 0.2.0
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.hetzner.api import (
    create_hetzner_argument_spec,
    create_hetzner_api,
)

from ansible_collections.community.dns.plugins.module_utils.module.record_info import (
    run_module,
    create_module_argument_spec,
)


def main():
    argument_spec = create_hetzner_argument_spec()
    argument_spec.merge(create_module_argument_spec(zone_id_type='str'))
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hetzner_api(module))


if __name__ == '__main__':
    main()
