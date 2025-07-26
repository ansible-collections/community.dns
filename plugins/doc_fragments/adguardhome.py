# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    CONNECTIVITY = r'''
options:
  username:
    description:
      - AdGuard Home user.
    required: true
    type: str
  password:
    description:
      - Related password for the AdGuard Home user
    required: true
    type: str
  host:
    description:
      - URL of AdGuard Home host.
      - For example, V(https://my-adguard.my-domain) or V(http://192.168.1.2).
    required: true
    type: str
  validate_certs:
    description:
      - Ability to skip ssl verification
    required: false
    type: bool
    default: true
requirements:
  - requests
  - yaml
'''
