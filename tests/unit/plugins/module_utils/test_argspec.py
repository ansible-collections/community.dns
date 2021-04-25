# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.argspec import (
    ArgumentSpec,
)


def test_argspec():
    empty = ArgumentSpec()
    non_empty = ArgumentSpec(
        argument_spec=dict(test=dict(type='str'), foo=dict()),
        required_together=[('test', 'foo')],
        required_if=[('test', 'bar', ['foo'])],
        required_one_of=[('test', 'foo')],
        mutually_exclusive=[('test', 'foo')]
    )
    empty.merge(non_empty)
    assert empty.to_kwargs() == non_empty.to_kwargs()
