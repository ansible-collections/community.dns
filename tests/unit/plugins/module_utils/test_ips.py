# -*- coding: utf-8 -*-
# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils import ips
from ansible_collections.community.dns.plugins.module_utils.ips import (
    assert_requirements_present,
    is_ip_address,
)


# We need ipaddress
ipaddress = pytest.importorskip('ipaddress')


def test_assert_requirements_present():
    class ModuleFailException(Exception):
        pass

    class FakeModule(object):
        def fail_json(self, **kwargs):
            raise ModuleFailException(kwargs)

    module = FakeModule()

    orig_importerror = ips.IPADDRESS_IMPORT_EXC
    try:
        ips.IPADDRESS_IMPORT_EXC = None
        assert_requirements_present(module)

        ips.IPADDRESS_IMPORT_EXC = 'asdf'
        with pytest.raises(ModuleFailException) as exc:
            assert_requirements_present(module)

        assert 'ipaddress' in exc.value.args[0]['msg']
        assert 'asdf' == exc.value.args[0]['exception']

    finally:
        ips.IPADDRESS_IMPORT_EXC = orig_importerror


IS_IP_ADDRESS_DATA = [
    ('foo.bar', False),
    ('foo', False),
    ('123', False),
    ('1.2.3.4', True),
    ('::', True),
]


@pytest.mark.parametrize("input_string, output", IS_IP_ADDRESS_DATA)
def test_is_ip_address(input_string, output):
    assert is_ip_address(input_string) == output
