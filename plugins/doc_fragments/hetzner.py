# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
options:
    hetzner_token:
        description:
          - The token for the Hetzner API.
          - If not provided, will be read from the environment variable C(HETZNER_DNS_TOKEN).
        aliases:
          - api_token
        type: str
        required: true
'''
