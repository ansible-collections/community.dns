# -*- coding: utf-8 -*-
#
# Copyright (c) 2017-2020 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    # Standard files documentation fragment
    DOCUMENTATION = r'''
requirements:
    - lxml

options:
    hosttech_username:
        description:
        - The username for the Hosttech API user.
        required: yes
        type: str
    hosttech_password:
        description:
        - The password for the Hosttech API user.
        required: yes
        type: str
'''
