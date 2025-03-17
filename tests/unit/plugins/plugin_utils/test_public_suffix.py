# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this file contains some public domain test data from
# https://raw.githubusercontent.com/publicsuffix/list/master/tests/test_psl.txt
# The data is marked and documented as public domain appropriately.

from __future__ import annotations

import typing as t

import pytest
from ansible_collections.community.dns.plugins.plugin_utils.public_suffix import (
    PUBLIC_SUFFIX_LIST,
    PublicSuffixList,
)


TEST_GET_SUFFIX = [
    ("", {}, {}, "", ""),
    (".", {}, {}, "", ""),
    ("foo.com", {}, {}, "com", "foo.com"),
    ("bar.foo.com.", {}, {}, "com.", "foo.com."),
    ("BaR.fOo.CoM.", {"normalize_result": True}, {}, "com.", "foo.com."),
    ("BaR.fOo.CoM.", {}, {}, "CoM.", "fOo.CoM."),
    ("com", {}, {}, "com", ""),
    ("com", {}, {"only_if_registerable": False}, "com", "com"),
    ("com", {"keep_unknown_suffix": False}, {}, "com", ""),
    ("foo.com", {}, {}, "com", "foo.com"),
    ("foo.com", {"keep_unknown_suffix": False}, {}, "com", "foo.com"),
    ("foobarbaz", {}, {}, "foobarbaz", ""),
    ("foobarbaz", {}, {"only_if_registerable": False}, "foobarbaz", "foobarbaz"),
    ("foobarbaz", {"keep_unknown_suffix": False}, {}, "", ""),
    ("foo.foobarbaz", {}, {}, "foobarbaz", "foo.foobarbaz"),
    ("foo.foobarbaz", {"keep_unknown_suffix": False}, {}, "", ""),
    ("-a.com", {}, {}, "", ""),  # invalid domain name (leading dash in label)
    ("a-.com", {}, {}, "", ""),  # invalid domain name (trailing dash in label)
    (
        "-.com",
        {},
        {},
        "",
        "",
    ),  # invalid domain name (leading and trailing dash in label)
    (".com", {}, {}, "", ""),  # invalid domain name (empty label)
    (
        "test.cloudfront.net",
        {},
        {},
        "cloudfront.net",
        "test.cloudfront.net",
    ),  # private rule
    ("test.cloudfront.net", {"icann_only": True}, {}, "net", "cloudfront.net"),
]


@pytest.mark.parametrize(
    "domain, kwargs, reg_extra_kwargs, suffix, reg_domain", TEST_GET_SUFFIX
)
def test_get_suffix(
    domain: str,
    kwargs: dict[str, t.Any],
    reg_extra_kwargs: dict[str, t.Any],
    suffix: str,
    reg_domain: str,
) -> None:
    assert PUBLIC_SUFFIX_LIST.get_suffix(domain, **kwargs) == suffix
    kwargs.update(reg_extra_kwargs)
    assert PUBLIC_SUFFIX_LIST.get_registrable_domain(domain, **kwargs) == reg_domain


# -------------------------------------------------------------------------------------------------
# The following list is taken from https://raw.githubusercontent.com/publicsuffix/list/master/tests/test_psl.txt
# Any copyright for this list is dedicated to the Public Domain. (https://creativecommons.org/publicdomain/zero/1.0/)
# This list has been provided by Rob Stradling of Comodo (see last section on https://publicsuffix.org/list/).
TEST_SUFFIX_OFFICIAL_TESTS = [
    # '' input.
    ("", "", {}),
    # Mixed case.
    ("COM", "", {}),
    ("example.COM", "example.com", {"normalize_result": True}),
    ("WwW.example.COM", "example.com", {"normalize_result": True}),
    ("example.COM", "example.COM", {}),
    ("WwW.example.COM", "example.COM", {}),
    # Leading dot.
    (".com", "", {}),
    (".example", "", {}),
    (".example.com", "", {}),
    (".example.example", "", {}),
    # Unlisted TLD.
    ("example", "", {}),
    ("example.example", "example.example", {}),
    ("b.example.example", "example.example", {}),
    ("a.b.example.example", "example.example", {}),
    # Listed, but non-Internet, TLD.
    # ('local', '', {}),
    # ('example.local', '', {}),
    # ('b.example.local', '', {}),
    # ('a.b.example.local', '', {}),
    # TLD with only 1 rule.
    ("biz", "", {}),
    ("domain.biz", "domain.biz", {}),
    ("b.domain.biz", "domain.biz", {}),
    ("a.b.domain.biz", "domain.biz", {}),
    # TLD with some 2-level rules.
    ("com", "", {}),
    ("example.com", "example.com", {}),
    ("b.example.com", "example.com", {}),
    ("a.b.example.com", "example.com", {}),
    ("uk.com", "", {}),
    ("example.uk.com", "example.uk.com", {}),
    ("b.example.uk.com", "example.uk.com", {}),
    ("a.b.example.uk.com", "example.uk.com", {}),
    ("test.ac", "test.ac", {}),
    # TLD with only 1 (wildcard) rule.
    ("mm", "", {}),
    ("c.mm", "", {}),
    ("b.c.mm", "b.c.mm", {}),
    ("a.b.c.mm", "b.c.mm", {}),
    # More complex TLD.
    ("jp", "", {}),
    ("test.jp", "test.jp", {}),
    ("www.test.jp", "test.jp", {}),
    ("ac.jp", "", {}),
    ("test.ac.jp", "test.ac.jp", {}),
    ("www.test.ac.jp", "test.ac.jp", {}),
    ("kyoto.jp", "", {}),
    ("test.kyoto.jp", "test.kyoto.jp", {}),
    ("ide.kyoto.jp", "", {}),
    ("b.ide.kyoto.jp", "b.ide.kyoto.jp", {}),
    ("a.b.ide.kyoto.jp", "b.ide.kyoto.jp", {}),
    ("c.kobe.jp", "", {}),
    ("b.c.kobe.jp", "b.c.kobe.jp", {}),
    ("a.b.c.kobe.jp", "b.c.kobe.jp", {}),
    ("city.kobe.jp", "city.kobe.jp", {}),
    ("www.city.kobe.jp", "city.kobe.jp", {}),
    # TLD with a wildcard rule and exceptions.
    ("ck", "", {}),
    ("test.ck", "", {}),
    ("b.test.ck", "b.test.ck", {}),
    ("a.b.test.ck", "b.test.ck", {}),
    ("www.ck", "www.ck", {}),
    ("www.www.ck", "www.ck", {}),
    # US K12.
    ("us", "", {}),
    ("test.us", "test.us", {}),
    ("www.test.us", "test.us", {}),
    ("ak.us", "", {}),
    ("test.ak.us", "test.ak.us", {}),
    ("www.test.ak.us", "test.ak.us", {}),
    ("k12.ak.us", "", {}),
    ("test.k12.ak.us", "test.k12.ak.us", {}),
    ("www.test.k12.ak.us", "test.k12.ak.us", {}),
    # IDN labels.
    ("食狮.com.cn", "食狮.com.cn", {}),
    ("食狮.公司.cn", "食狮.公司.cn", {}),
    ("www.食狮.公司.cn", "食狮.公司.cn", {}),
    ("shishi.公司.cn", "shishi.公司.cn", {}),
    ("公司.cn", "", {}),
    ("食狮.中国", "食狮.中国", {}),
    ("www.食狮.中国", "食狮.中国", {}),
    ("shishi.中国", "shishi.中国", {}),
    ("中国", "", {}),
    # Same as above, but punycoded.  (TODO: punycode not supported yet!)
    ("xn--85x722f.com.cn", "xn--85x722f.com.cn", {}),
    ("xn--85x722f.xn--55qx5d.cn", "xn--85x722f.xn--55qx5d.cn", {}),
    ("www.xn--85x722f.xn--55qx5d.cn", "xn--85x722f.xn--55qx5d.cn", {}),
    ("shishi.xn--55qx5d.cn", "shishi.xn--55qx5d.cn", {}),
    ("xn--55qx5d.cn", "", {}),
    ("xn--85x722f.xn--fiqs8s", "xn--85x722f.xn--fiqs8s", {}),
    ("www.xn--85x722f.xn--fiqs8s", "xn--85x722f.xn--fiqs8s", {}),
    ("shishi.xn--fiqs8s", "shishi.xn--fiqs8s", {}),
    ("xn--fiqs8s", "", {}),
]
# End of public domain test data
# -------------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "domain, registrable_domain, kwargs", TEST_SUFFIX_OFFICIAL_TESTS
)
def test_get_suffix_official(
    domain: str, registrable_domain: str, kwargs: dict[str, t.Any]
) -> None:
    reg_domain = PUBLIC_SUFFIX_LIST.get_registrable_domain(domain, **kwargs)
    assert reg_domain == registrable_domain


def test_load_psl_dot(tmpdir) -> None:
    fn = tmpdir / "psl.dat"
    fn.write(
        """// ===BEGIN BLA BLA DOMAINS===
.com.
// ===END BLA BLA DOMAINS===""".encode(
            "utf-8"
        )
    )
    psl = PublicSuffixList.load(str(fn))
    assert len(psl._rules) == 1
    rule = psl._rules[0]
    assert rule.labels == ("com",)
    assert rule.exception_rule is False
    assert rule.part == "bla bla"


def test_load_psl_no_part(tmpdir) -> None:
    fn = tmpdir / "psl.dat"
    fn.write(
        """// ===BEGIN BLA BLA DOMAINS===
com
// ===END BLA BLA DOMAINS===
net""".encode(
            "utf-8"
        )
    )
    with pytest.raises(Exception) as excinfo:
        PublicSuffixList.load(str(fn))
    assert str(excinfo.value) == "Internal error: found PSL entry with no part!"
