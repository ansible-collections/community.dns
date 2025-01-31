# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils.provider import ensure_type


CHECK_TYPE_DATA = [
    ('asdf', 'str', 'asdf'),
    (1, 'str', '1'),
    ([], 'list', []),
    ({}, 'dict', {}),
    ('yes', 'bool', True),
    ('5', 'int', 5),
    ('5.10', 'float', 5.10),
    ('foobar', 'raw', 'foobar'),
]


@pytest.mark.parametrize("input_string, type_name, output", CHECK_TYPE_DATA)
def test_is_ascii_label(input_string, type_name, output):
    assert ensure_type(input_string, type_name) == output
