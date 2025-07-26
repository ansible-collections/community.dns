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
      - IP or FQDN of AdGuard Home host.
      - Requires also the protocol (http:// or https://).
    required: true
    type: str
  ssl_verify:
    description:
      - ability to skip ssl verification
    required: false
    type: bool
    default: true
requirements:
  - requests
  - yaml
'''
