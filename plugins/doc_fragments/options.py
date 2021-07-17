# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ModuleDocFragment(object):

    BULK_OPERATIONS = r'''
options:
    bulk_operation_threshold:
        description:
            - Determines the threshold from when on bulk operations are used.
            - The default value 2 means that if 2 or more operations of a kind are planned,
              and the API supports bulk operations for this kind of operation, they will
              be used.
        type: int
        default: 2
'''
