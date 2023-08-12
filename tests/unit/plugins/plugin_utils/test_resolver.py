# -*- coding: utf-8 -*-
# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible.errors import AnsibleError

from ansible_collections.community.dns.plugins.plugin_utils import resolver

from ansible_collections.community.dns.plugins.plugin_utils.resolver import (
    assert_requirements_present,
)


def test_assert_requirements_present():
    orig_importerror = resolver.DNSPYTHON_IMPORTERROR
    try:
        resolver.DNSPYTHON_IMPORTERROR = None
        assert_requirements_present('community.dns.foo', 'lookup')

        resolver.DNSPYTHON_IMPORTERROR = Exception('asdf')
        with pytest.raises(AnsibleError) as exc:
            assert_requirements_present('community.dns.foo', 'lookup')

        assert 'dnspython' in exc.value.args[0]

    finally:
        resolver.DNSPYTHON_IMPORTERROR = orig_importerror
