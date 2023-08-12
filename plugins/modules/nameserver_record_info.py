#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: nameserver_record_info
short_description: Look up all records of a type from all nameservers for a DNS name
version_added: 2.6.0
description:
    - Given a DNS name and a record type, will retrieve all nameservers that are responsible for
      this DNS name, and from them all records for this name of the given type.
extends_documentation_fragment:
    - community.dns.attributes
    - community.dns.attributes.info_module
author:
    - Felix Fontein (@felixfontein)
options:
    name:
        description:
            - A list of DNS names whose nameservers to retrieve.
        required: true
        type: list
        elements: str
    type:
        description:
            - The record type to retrieve.
        required: true
        type: str
        choices:
            - A
            - ALL
            - AAAA
            - CAA
            - CNAME
            - DNAME
            - DNSKEY
            - DS
            - HINFO
            - LOC
            - MX
            - NAPTR
            - NS
            - NSEC
            - NSEC3
            - NSEC3PARAM
            - PTR
            - RP
            - RRSIG
            - SOA
            - SPF
            - SRV
            - SSHFP
            - TLSA
            - TXT
    query_retry:
        description:
            - Number of retries for DNS query timeouts.
        type: int
        default: 3
    query_timeout:
        description:
            - Timeout per DNS query in seconds.
        type: float
        default: 10
    always_ask_default_resolver:
        description:
            - When set to V(true) (default), will use the default resolver to find the authoritative nameservers
              of a subzone.
            - When set to V(false), will use the authoritative nameservers of the parent zone to find the
              authoritative nameservers of a subzone. This only makes sense when the nameservers were recently
              changed and have not yet propagated.
        type: bool
        default: true
    servfail_retries:
        description:
            - How often to retry on SERVFAIL errors.
        type: int
        default: 0
requirements:
    - dnspython >= 1.15.0 (maybe older versions also work)
notes:
    - dnspython before 2.0.0 does not correctly support (un-)escaping UTF-8 in TXT-like records. This can
      result in wrongly decoded TXT records. Please use dnspython 2.0.0 or later to fix this issue; see also
      U(https://github.com/rthalley/dnspython/issues/321).
      Unfortunately dnspython 2.0.0 requires Python 3.6 or newer.
'''

EXAMPLES = r'''
- name: Retrieve TXT values from all nameservers for two DNS names
  community.dns.nameserver_record_info:
    name:
      - www.example.com
      - example.org
    type: TXT
  register: result

- name: Show TXT values for www.example.com for all nameservers
  ansible.builtin.debug:
    msg: '{{ result.results[0].result }}'
'''

RETURN = r'''
results:
    description:
        - Information on the records for every DNS name provided in O(name).
    returned: always
    type: list
    elements: dict
    contains:
        name:
            description:
                - The DNS name this entry is for.
            returned: always
            type: str
            sample: www.example.com
        result:
            description:
                - A list of values per nameserver.
            returned: success
            type: list
            elements: dict
            sample:
                - nameserver: ns1.example.com
                  values:
                    - X
                - nameserver: ns2.example.com
                  values:
                    - X
            contains:
                nameserver:
                    description:
                        - The nameserver.
                    returned: success
                    type: str
                    sample: ns1.example.com
                values:
                    description:
                        - The records of type O(type).
                        - Depending on O(type), different fields are returned.
                        - For O(type=TXT) and O(type=SPF), also the concatenated value is returned as RV(results[].result[].values[].value).
                    returned: success
                    type: list
                    elements: dict
                    sample:
                        - address: 127.0.0.1
                    contains:
                        address:
                            description:
                                - A IPv4 respectively IPv6 address.
                            type: str
                            returned: if O(type=A) or O(type=AAAA)
                        algorithm:
                            description:
                                - The algorithm ID.
                            type: int
                            returned: if O(type=DNSKEY) or O(type=DS) or O(type=NSEC3) or O(type=NSEC3PARAM) or O(type=RRSIG) or O(type=SSHFP)
                        altitude:
                            description:
                                - The altitute.
                            type: float
                            returned: if O(type=LOC)
                        cert:
                            description:
                                - The certificate.
                            type: str
                            returned: if O(type=TLSA)
                        cpu:
                            description:
                                - The CPU.
                            type: str
                            returned: if O(type=HINFO)
                        digest:
                            description:
                                - The digest.
                            type: str
                            returned: if O(type=DS)
                        digest_type:
                            description:
                                - The digest's type.
                            type: int
                            returned: if O(type=DS)
                        exchange:
                            description:
                                - The exchange server.
                            type: str
                            returned: if O(type=MX)
                        expiration:
                            description:
                                - The expiration Unix timestamp.
                            type: int
                            returned: if O(type=RRSIG)
                        expire:
                            description:
                                - Number of seconds after which secondary name servers should stop answering request
                                  for this zone if the main name server does not respond.
                            type: int
                            returned: if O(type=SOA)
                        fingerprint:
                            description:
                                - The fingerprint.
                            type: str
                            returned: if O(type=SSHFP)
                        flags:
                            description:
                                - Flags.
                                - This is actually of type C(string) for O(type=NAPTR).
                            type: int
                            returned: if O(type=CAA) or O(type=DNSKEY) or O(type=NAPTR) or O(type=NSEC3) or O(type=NSEC3PARAM)
                        fp_type:
                            description:
                                - The fingerprint's type.
                            type: int
                            returned: if O(type=SSHFP)
                        horizontal_precision:
                            description:
                                - The horizontal precision of the location.
                            type: float
                            returned: if O(type=LOC)
                        inception:
                            description:
                                - The inception Unix timestamp.
                            type: int
                            returned: if O(type=RRSIG)
                        iterations:
                            description:
                                - The number of iterations.
                            type: int
                            returned: if O(type=NSEC3) or O(type=NSEC3PARAM)
                        key:
                            description:
                                - The key.
                            type: str
                            returned: if O(type=DNSKEY)
                        key_tag:
                            description:
                                - The key's tag.
                            type: int
                            returned: if O(type=DS) or O(type=RRSIG)
                        labels:
                            description:
                                - The labels.
                            type: int
                            returned: if O(type=RRSIG)
                        latitude:
                            description:
                                - The location's latitude.
                            type: list
                            elements: int
                            returned: if O(type=LOC)
                        longitude:
                            description:
                                - The location's longitude.
                            type: list
                            elements: int
                            returned: if O(type=LOC)
                        mbox:
                            description:
                                - The mbox.
                            type: str
                            returned: if O(type=RP)
                        minimum:
                            description:
                                - Used to calculate the TTL for purposes of negative caching.
                            type: int
                            returned: if O(type=SOA)
                        mname:
                            description:
                                - Primary main name server for this zone.
                            type: str
                            returned: if O(type=SOA)
                        mtype:
                            description:
                                - The mtype.
                            type: int
                            returned: if O(type=TLSA)
                        next:
                            description:
                                - The next value.
                            type: str
                            returned: if O(type=NSEC) or O(type=NSEC3)
                        order:
                            description:
                                - The order value.
                            type: int
                            returned: if O(type=NAPTR)
                        original_ttl:
                            description:
                                - The original TTL.
                            type: int
                            returned: if O(type=RRSIG)
                        os:
                            description:
                                - The operating system.
                            type: str
                            returned: if O(type=HINFO)
                        port:
                            description:
                                - The port.
                            type: int
                            returned: if O(type=SRV)
                        preference:
                            description:
                                - The preference value for this record.
                            type: int
                            returned: if O(type=MX) or O(type=NAPTR)
                        priority:
                            description:
                                - The priority value for this record.
                            type: int
                            returned: if O(type=SRV)
                        protocol:
                            description:
                                - The protocol.
                            type: int
                            returned: if O(type=DNSKEY)
                        refresh:
                            description:
                                - Number of seconds after which secondary name servers should query the main
                                  name server for the SOA record to detect zone changes.
                            type: int
                            returned: if O(type=SOA)
                        regexp:
                            description:
                                - A regular expression.
                            type: str
                            returned: if O(type=NAPTR)
                        replacement:
                            description:
                                - The replacement.
                            type: str
                            returned: if O(type=NAPTR)
                        retry:
                            description:
                                - Number of seconds after which secondary name servers should retry to request
                                  the serial number from the main name server if the main name server does not respond.
                            type: int
                            returned: if O(type=SOA)
                        rname:
                            description:
                                - E-mail address of the administrator responsible for this zone.
                            type: str
                            returned: if O(type=SOA)
                        salt:
                            description:
                                - The salt.
                            type: str
                            returned: if O(type=NSEC3) or O(type=NSEC3PARAM)
                        selector:
                            description:
                                - The selector.
                            type: int
                            returned: if O(type=TLSA)
                        serial:
                            description:
                                - Serial number for this zone.
                            type: int
                            returned: if O(type=SOA)
                        service:
                            description:
                                - The service.
                            type: str
                            returned: if O(type=NAPTR)
                        signature:
                            description:
                                - The signature.
                            type: str
                            returned: if O(type=RRSIG)
                        signer:
                            description:
                                - The signer.
                            type: str
                            returned: if O(type=RRSIG)
                        size:
                            description:
                                - The size of the location.
                            type: float
                            returned: if O(type=LOC)
                        strings:
                            description:
                                - List of strings for this record.
                                - See RV(results[].result[].values[].value) for the concatenated result.
                            type: list
                            elements: str
                            returned: if O(type=SPF) or O(type=TXT)
                        tag:
                            description:
                                - The tag.
                            type: str
                            returned: if O(type=CAA)
                        target:
                            description:
                                - The target.
                            type: str
                            returned: if O(type=CNAME) or O(type=DNAME) or O(type=NS) or O(type=PTR) or O(type=SRV)
                        txt:
                            description:
                                - The TXT value.
                            type: str
                            returned: if O(type=RP)
                        type_covered:
                            description:
                                - The type covered.
                            type: str
                            returned: if O(type=RRSIG)
                        usage:
                            description:
                                - The usage flag.
                            type: int
                            returned: if O(type=TLSA)
                        value:
                            description:
                                - The value.
                                - For O(type=SPF) or O(type=TXT), this is the concatenation of RV(results[].result[].values[].strings).
                            type: str
                            returned: if O(type=CAA) or O(type=SPF) or O(type=TXT)
                        vertical_precision:
                            description:
                                - The vertical precision of the location.
                            type: float
                            returned: if O(type=LOC)
                        weight:
                            description:
                                - The service's weight.
                            type: int
                            returned: if O(type=SRV)
                        windows:
                            description:
                                - The windows.
                            type: str
                            returned: if O(type=NSEC) or O(type=NSEC3)
    sample:
        - name: www.example.com
          result:
            - nameserver: ns1.example.com
              values:
                - address: 127.0.0.1
            - nameserver: ns2.example.com
              values:
                - address: 127.0.0.1
        - name: example.org
          result:
            - nameserver: ns1.example.org
              values:
                - address: 127.0.0.1
                - address: 127.0.0.2
            - nameserver: ns2.example.org
              values:
                - address: 127.0.0.2
            - nameserver: ns3.example.org
              values:
                - address: 127.0.0.1
'''

from ansible.module_utils.basic import AnsibleModule

from ansible_collections.community.dns.plugins.module_utils.resolver import (
    ResolveDirectlyFromNameServers,
    assert_requirements_present,
    guarded_run,
)

from ansible_collections.community.dns.plugins.module_utils.dnspython_records import (
    NAME_TO_RDTYPE,
    convert_rdata_to_dict,
)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='list', elements='str'),
            type=dict(
                required=True,
                type='str',
                choices=[
                    'A',
                    'ALL',
                    'AAAA',
                    'CAA',
                    'CNAME',
                    'DNAME',
                    'DNSKEY',
                    'DS',
                    'HINFO',
                    'LOC',
                    'MX',
                    'NAPTR',
                    'NS',
                    'NSEC',
                    'NSEC3',
                    'NSEC3PARAM',
                    'PTR',
                    'RP',
                    'RRSIG',
                    'SOA',
                    'SPF',
                    'SRV',
                    'SSHFP',
                    'TLSA',
                    'TXT',
                ],
            ),
            query_retry=dict(type='int', default=3),
            query_timeout=dict(type='float', default=10),
            always_ask_default_resolver=dict(type='bool', default=True),
            servfail_retries=dict(type='int', default=0),
        ),
        supports_check_mode=True,
    )
    assert_requirements_present(module)

    names = module.params['name']
    record_type = module.params['type']

    resolver = ResolveDirectlyFromNameServers(
        timeout=module.params['query_timeout'],
        timeout_retries=module.params['query_retry'],
        servfail_retries=module.params['servfail_retries'],
        always_ask_default_resolver=module.params['always_ask_default_resolver'],
    )
    results = [None] * len(names)
    for index, name in enumerate(names):
        results[index] = {
            'name': name,
        }

    rdtype = NAME_TO_RDTYPE[record_type]

    def f():
        for index, name in enumerate(names):
            result = []
            results[index]['result'] = result
            records_for_nameservers = resolver.resolve(name, rdtype=rdtype)
            for nameserver, records in records_for_nameservers.items():
                ns_result = {
                    'nameserver': nameserver,
                }
                result.append(ns_result)
                values = []
                if records is not None:
                    for data in records:
                        values.append(convert_rdata_to_dict(data))
                ns_result['values'] = sorted(values)
            result.sort(key=lambda v: v['nameserver'])

    guarded_run(f, module, generate_additional_results=lambda: dict(results=results))
    module.exit_json(results=results)


if __name__ == "__main__":
    main()
