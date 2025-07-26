#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2025 Markus Bergholz
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r"""
module: adguardhome_rewrite

short_description: Add, update or delete DNS rewrite rules from AdGuard Home

version_added: 3.3.0

description:
  - Add, update or delete DNS rewrite rules from AdGuard Home.
extends_documentation_fragment:
  - community.dns.adguardhome.connectivity
  - community.dns.attributes
options:
  state:
    description:
      - wether a rewrite rule should be added/updated O(state=present) or removed O(state=absent).
    type: str
    default: present
    choices:
      - present
      - absent
  domain:
    description:
      - domain or wildcard domain that you want to be rewritten by AdGuard Home.
    type: str
    required: true
  answer:
    description:
      - value for the domain rewrite.
      - required when O(state=present).
      - value can be a CNAME, A or AAAA record.
    type: str
    required: false
attributes:
  check_mode:
    support: full
    description: Can run in C(check_mode) and return changed status prediction without modifying target.
    details:
      - This action does not modify state.
  diff_mode:
    support: full
    description: Will return details on what has changed (or possibly needs changing in C(check_mode)), when in diff mode.
  idempotent:
    support: full
    description:
      - When run twice in a row outside check mode, with the same arguments, the second invocation indicates no change.
      - This assumes that the system controlled/queried by the module has not changed in a relevant way.


author:
  - Markus Bergholz (@markuman) <markuman+spambelongstogoogle@gmail.com>
"""

EXAMPLES = r"""
- name: add dns rewrite rule in adguard home
  community.dns.adguardhome_rewrite:
    state: present
    answer: 127.0.0.1
    domain: example.org

# when removing a rewrite, the current answer value must also match
# therefore you can just leave it out and the existing value
# will be used
- name: remove rewrite for example.org
  community.dns.adguardhome_rewrite:
    state: absent
    domain: example.org
"""

RETURN = r"""
rules:
  description: The list of fetched rewrite rules.
  type: list
  elements: dict
  returned: always
  contains:
    answer:
      description: Value of the rewrite.
      type: str
      sample: 192.168.178.71
    domain:
      description: Domain of the rewrite.
      type: str
      sample: dns.osuv.de
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import missing_required_lib
from ansible_collections.community.dns.plugins.module_utils.adguardhome.api import (
    AdGuardHomeAPIHandler
)
import traceback

YAML_IMP_ERR = None
try:
    import yaml
    HAS_YAML = True
except Exception:
    YAML_IMP_ERR = traceback.format_exc()
    HAS_YAML = False


def find_and_compare(rules, domain, answer):
    domain_exists = False
    value_is_different = False
    target = {}
    for rule in rules:
        if rule["domain"] == domain:
            domain_exists = True
            target = {"domain": domain, "answer": rule["answer"]}
            if rule["answer"] != answer:
                value_is_different = True
            break
    return domain_exists, value_is_different, target


def main():
    module = AnsibleModule(
        argument_spec=dict(
            username=dict(type='str', required=True),
            password=dict(type='str', required=True, no_log=True),
            host=dict(type='str', required=True),
            ssl_verify=dict(type='bool', default=True),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            answer=dict(type='str', required=False),
            domain=dict(type='str', required=True),
        ),
        supports_check_mode=True,
        required_if=[['state', 'present', ['answer']]],
    )

    if not HAS_YAML:
        module.fail_json(
            msg=missing_required_lib("pyyaml", url='https://pyyaml.org/wiki/PyYAMLDocumentation'),
            exception=YAML_IMP_ERR
        )

    domain = module.params.get('domain')
    answer = module.params.get('answer')
    state = module.params.get('state')

    adguardhome = AdGuardHomeAPIHandler(module.params, module.fail_json)

    before = adguardhome.list()
    changed = False

    DOMAIN_EXISTS, VALUE_IS_DIFFERENT, TARGET = find_and_compare(before, domain, answer)
    if state == 'present':
        if not DOMAIN_EXISTS and not module.check_mode and not VALUE_IS_DIFFERENT:
            changed = True
            if module.check_mode:
                checked_mode_after = before + [{"answer": answer, "domain": domain}]
            else:
                adguardhome.add_or_delete(domain, answer, "add", TARGET)

        if DOMAIN_EXISTS and VALUE_IS_DIFFERENT:
            changed = True
            adguardhome.update(domain, answer, TARGET)

    else:
        if DOMAIN_EXISTS and not module.check_mode:
            adguardhome.add_or_delete(domain, answer, "delete", TARGET)
            changed = True

    after = adguardhome.list()

    diff_item = dict(
        before=yaml.safe_dump(before),
        after=yaml.safe_dump(after)
    )

    module.exit_json(changed=changed, diff=diff_item)


if __name__ == '__main__':
    main()
