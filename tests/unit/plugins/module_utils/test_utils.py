# -*- coding: utf-8 -*-
# Copyright (c) 2025, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


from .utils import patch_dict, patch_dict_absent


def test_patch_dict():
    a = {1: True}
    assert a[1] is True
    assert 2 not in a
    with patch_dict(a, 1, False):
        assert a[1] is False
        assert 2 not in a
    assert a[1] is True
    assert 2 not in a
    with patch_dict(a, 2, False):
        assert a[1] is True
        assert a[2] is False
    assert a[1] is True
    assert 2 not in a


def test_patch_dict_absent():
    a = {1: True}
    assert a[1] is True
    assert 2 not in a
    with patch_dict_absent(a, 1):
        assert 1 not in a
        assert 2 not in a
    assert a[1] is True
    assert 2 not in a
    with patch_dict_absent(a, 2):
        assert a[1] is True
        assert 2 not in a
    assert a[1] is True
    assert 2 not in a
