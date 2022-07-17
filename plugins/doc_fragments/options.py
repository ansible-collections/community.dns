# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

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

    RECORD_TRANSFORMATION = r'''
options:
    txt_transformation:
        description:
            - Determines how TXT entry values are converted between the API and this module's
              input and output.
            - The value C(api) means that values are returned from this module as they are returned
              from the API, and pushed to the API as they have been passed to this module. For
              idempotency checks, the input string will be compared to the strings returned by the
              API. The API might automatically transform some values, like splitting long values or
              adding quotes, which can cause problems with idempotency.
            - The value C(unquoted) automatically transforms values so that you can pass in unquoted
              values, and the module will return unquoted values. If you pass in quoted values, they
              will be double-quoted.
            - The value C(quoted) automatically transforms values so that you must use quoting for values
              that contain spaces, characters such as quotation marks and backslashes, and that are
              longer than 255 bytes. It also makes sure to return values from the API in a normalized
              encoding.
            - The default value, C(unquoted), ensures that you can work with values without having
              to care about how to correctly quote for DNS. Most users should use one of C(unquoted)
              or C(quoted), but not C(api).
            - B(Note:) the conversion code assumes UTF-8 encoding for values. If you need another
              encoding use I(txt_transformation=api) and handle the encoding yourself.
        type: str
        choices:
            - api
            - quoted
            - unquoted
        default: unquoted
'''
