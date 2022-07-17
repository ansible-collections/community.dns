# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.names import (
    join_labels,
    is_ascii_label,
    normalize_label,
    split_into_labels,
    InvalidDomainName,
)


TEST_IS_ASCII_LABEL = [
    ('asdf', True),
    ('', True),
    ('ä', False),
    ('☹', False),
    ('_dmarc', True),
]


@pytest.mark.parametrize("domain, result", TEST_IS_ASCII_LABEL)
def test_is_ascii_label(domain, result):
    assert is_ascii_label(domain) == result


TEST_LABEL_SPLIT = [
    ('', [], ''),
    ('.', [], '.'),
    ('com', ['com'], ''),
    ('com.', ['com'], '.'),
    ('foo.bar', ['bar', 'foo'], ''),
    ('foo.bar.', ['bar', 'foo'], '.'),
    ('*.bar.', ['bar', '*'], '.'),
    (u'☺.A', ['A', u'☺'], ''),
]


@pytest.mark.parametrize("domain, labels, tail", TEST_LABEL_SPLIT)
def test_split_into_labels(domain, labels, tail):
    _labels, _tail = split_into_labels(domain)
    assert _labels == labels
    assert _tail == tail
    assert join_labels(_labels, _tail) == domain


TEST_LABEL_SPLIT_ERRORS = [
    '.bar.',
    '..bar',
    '-bar',
    'bar-',
]


@pytest.mark.parametrize("domain", TEST_LABEL_SPLIT_ERRORS)
def test_split_into_labels_errors(domain):
    with pytest.raises(InvalidDomainName):
        split_into_labels(domain)


TEST_LABEL_JOIN = [
    ([], '', ''),
    ([], '.', '.'),
    (['a', 'b', 'c'], '', 'c.b.a'),
    (['a', 'b', 'c'], '.', 'c.b.a.'),
]


@pytest.mark.parametrize("labels, tail, result", TEST_LABEL_JOIN)
def test_join_labels(labels, tail, result):
    domain = join_labels(labels, tail)
    assert domain == result
    _labels, _tail = split_into_labels(domain)
    assert _labels == labels
    assert _tail == tail


TEST_LABEL_NORMALIZE = [
    ('', ''),
    ('*', '*'),
    ('foo', 'foo'),
    ('Foo', 'foo'),
    ('_dmarc', '_dmarc'),
    (u'hëllö', 'xn--hll-jma1d'),
    (u'食狮', 'xn--85x722f'),
    (u'☺', 'xn--74h'),
    (u'😉', 'xn--n28h'),
]


@pytest.mark.parametrize("label, normalized_label", TEST_LABEL_NORMALIZE)
def test_normalize_label(label, normalized_label):
    print(normalize_label(label))
    assert normalize_label(label) == normalized_label
