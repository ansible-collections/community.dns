# -*- coding: utf-8 -*-
# (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function

__metaclass__ = type


import pytest

from ansible_collections.community.dns.plugins.module_utils.names import (
    join_labels,
    only_alabels,
    normalize_label,
    split_into_labels,
    InvalidDomainName,
)


TEST_ONLY_ALABELS = [
    ('asdf', True),
    ('', True),
    ('ä', False),
    ('☹', False),
]


@pytest.mark.parametrize("domain, result", TEST_ONLY_ALABELS)
def test_only_alabels(domain, result):
    assert only_alabels(domain) == result


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
    (u'hëllö', 'xn--hll-jma1d'),
    (u'食狮', 'xn--85x722f'),
    (u'☺', 'xn--74h'),
    (u'😉', 'xn--n28h'),
]


@pytest.mark.parametrize("label, normalized_label", TEST_LABEL_NORMALIZE)
def test_normalize_label(label, normalized_label):
    print(normalize_label(label))
    assert normalize_label(label) == normalized_label
