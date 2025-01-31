# -*- coding: utf-8 -*-
# Copyright (c) 2024, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest
from ansible.utils.unsafe_proxy import AnsibleUnsafe
from ansible.utils.unsafe_proxy import wrap_var as ansible_make_unsafe
from ansible_collections.community.dns.plugins.plugin_utils.unsafe import make_unsafe


TEST_MAKE_UNSAFE = [
    (
        "text",
        [],
        [
            (),
        ],
    ),
    (
        "{{text}}",
        [
            (),
        ],
        [],
    ),
    (
        b"text",
        [],
        [
            (),
        ],
    ),
    (
        b"{{text}}",
        [
            (),
        ],
        [],
    ),
    (
        {
            "skey": "value",
            "ukey": "{{value}}",
            1: [
                "value",
                "{{value}}",
                {
                    1.0: "{{value}}",
                    2.0: "value",
                },
            ],
        },
        [
            ("ukey",),
            (1, 1),
            (1, 2, 1.0),
        ],
        [
            ("skey",),
            (1, 0),
            (1, 2, 2.0),
        ],
    ),
    (
        ["value", "{{value}}"],
        [
            (1,),
        ],
        [
            (0,),
        ],
    ),
]


@pytest.mark.parametrize(
    "value, check_unsafe_paths, check_safe_paths", TEST_MAKE_UNSAFE
)
def test_make_unsafe(value, check_unsafe_paths, check_safe_paths):
    unsafe_value = make_unsafe(value)
    assert unsafe_value == value
    for check_path in check_unsafe_paths:
        obj = unsafe_value
        for elt in check_path:
            obj = obj[elt]
        assert isinstance(obj, AnsibleUnsafe)
    for check_path in check_safe_paths:
        obj = unsafe_value
        for elt in check_path:
            obj = obj[elt]
        assert not isinstance(obj, AnsibleUnsafe)


def test_make_unsafe_idempotence():
    assert make_unsafe(None) is None

    unsafe_str = ansible_make_unsafe("{{test}}")
    assert id(make_unsafe(unsafe_str)) == id(unsafe_str)

    safe_str = "{{test}}"
    assert id(make_unsafe(safe_str)) != id(safe_str)


def test_make_unsafe_dict_key():
    value = {
        b"test": 1,
        "test": 2,
    }
    unsafe_value = make_unsafe(value)
    assert unsafe_value == value
    for obj in unsafe_value:
        assert not isinstance(obj, AnsibleUnsafe)

    value = {
        b"{{test}}": 1,
        "{{test}}": 2,
    }
    unsafe_value = make_unsafe(value)
    assert unsafe_value == value
    for obj in unsafe_value:
        assert isinstance(obj, AnsibleUnsafe)


def test_make_unsafe_set():
    value = set([b"test", "test"])
    unsafe_value = make_unsafe(value)
    assert unsafe_value == value
    for obj in unsafe_value:
        assert not isinstance(obj, AnsibleUnsafe)

    value = set([b"{{test}}", "{{test}}"])
    unsafe_value = make_unsafe(value)
    assert unsafe_value == value
    for obj in unsafe_value:
        assert isinstance(obj, AnsibleUnsafe)
