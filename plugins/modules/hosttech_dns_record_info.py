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

extends_documentation_fragment:
    - community.dns.hosttech
    - community.dns.module_record_info

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

from ansible_collections.community.dns.plugins.module_utils.hosttech.api import (
    create_hosttech_argument_spec,
    create_hosttech_api,
)

from ansible_collections.community.dns.plugins.module_utils.module.record import (
    run_module,
    create_module_argument_spec,
)


def main():
    argument_spec = create_hosttech_argument_spec()
    argument_spec.merge(create_module_argument_spec())
    module = AnsibleModule(supports_check_mode=True, **argument_spec.to_kwargs())
    run_module(module, lambda: create_hosttech_api(module))


if __name__ == '__main__':
    main()
