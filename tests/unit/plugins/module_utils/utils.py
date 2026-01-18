# -*- coding: utf-8 -*-
# Copyright (c) 2025, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import contextlib


@contextlib.contextmanager
def patch_dict(dictionary, key, value):
    has_key = key in dictionary
    old_value = dictionary.get(key)
    try:
        dictionary[key] = value
        yield
    finally:
        if has_key:
            dictionary[key] = old_value
        else:
            dictionary.pop(key, None)


@contextlib.contextmanager
def patch_dict_absent(dictionary, key):
    has_key = key in dictionary
    old_value = dictionary.get(key)
    try:
        dictionary.pop(key, None)
        yield
    finally:
        if has_key:
            dictionary[key] = old_value
