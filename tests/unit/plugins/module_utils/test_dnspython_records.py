# -*- coding: utf-8 -*-
# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


import pytest
from ansible_collections.community.dns.plugins.module_utils.dnspython_records import (
    RDTYPE_TO_FIELDS,
    convert_rdata_to_dict,
)


# We need dnspython
dns = pytest.importorskip('dns')

import dns.version


TEST_CONVERT_RDATA_TO_DICT = [
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'address': '3.3.3.3',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '1:2::3'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'address': '1:2::3',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.AAAA, '::'),
        {'to_unicode': False, 'add_synthetic': True},
        {
            'address': '::',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CAA, '10 issue letsencrypt.org'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'flags': 10,
            'tag': 'issue',
            'value': 'letsencrypt.org',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.CNAME, 'foo.example.com.'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'target': 'foo.example.com.',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.DNAME, 'foo.example.com.'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'target': 'foo.example.com.',
        },
    ),
    (
        dns.rdata.from_text(
            dns.rdataclass.IN,
            dns.rdatatype.DNSKEY,
            '512 255 1 AQMFD5raczCJHViKtLYhWGz8hMY9UGRuniJDBzC7w0aR yzWZriO6i2odGWWQVucZqKVsENW91IOW4vqudngPZsY3'
            ' GvQ/xVA8/7pyFj6b7Esga60zyGW6LFe9r8n6paHrlG5o jqf0BaqHT+8=',
        ),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'flags': 512,
            'algorithm': 1,
            'protocol': 255,
            'key': (
                'AQMFD5raczCJHViKtLYhWGz8hMY9UGRuniJDBzC7w0aRyzWZriO6i2odGWWQVucZqKVsENW9'
                '1IOW4vqudngPZsY3GvQ/xVA8/7pyFj6b7Esga60zyGW6LFe9r8n6paHrlG5ojqf0BaqHT+8='
            ),
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.DS, '12345 3 1 123456789abcdef67890123456789abcdef67890'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'algorithm': 3,
            'digest_type': 1,
            'key_tag': 12345,
            'digest': '123456789abcdef67890123456789abcdef67890',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.HINFO, '"Generic PC clone" "NetBSD-1.4"'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'cpu': b'Generic PC clone',
            'os': b'NetBSD-1.4',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.LOC, '60 9 0.000 N 24 39 0.000 E 10.00m 20.00m 2000.00m 20.00m'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'latitude': [60, 9, 0, 0, 1],
            'longitude': [24, 39, 0, 0, 1],
            'altitude': 1000.0,
            'size': 2000.0,
            'horizontal_precision': 200000.0,
            'vertical_precision': 2000.0,
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.MX, '10 mail.example.com'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'preference': 10,
            'exchange': 'mail.example.com',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NAPTR, '65535 65535 "text 1" "text 2" "text 3" example.com.'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'order': 65535,
            'preference': 65535,
            'flags': b'text 1',
            'service': b'text 2',
            'regexp': b'text 3',
            'replacement': 'example.com.',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NS, 'ns.example.org.'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'target': 'ns.example.org.',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NSEC, 'a.secure A MX RRSIG NSEC TYPE1234'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'next': 'a.secure',
            'windows': 'A MX RRSIG NSEC TYPE1234',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NSEC3, '1 1 123 f00baa23 2t7b4g4vsa5smi47k61mv5bv1a22bojr NS SOA MX RRSIG DNSKEY NSEC3PARAM'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'algorithm': 1,
            'flags': 1,
            'iterations': 123,
            'salt': 'f00baa23',
            'next': '2t7b4g4vsa5smi47k61mv5bv1a22bojr',
            'windows': 'NS SOA MX RRSIG DNSKEY NSEC3PARAM',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.NSEC3PARAM, '1 1 123 f00baa23'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'algorithm': 1,
            'flags': 1,
            'iterations': 123,
            'salt': 'f00baa23',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.PTR, 'example.com.'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'target': 'example.com.',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.RP, 'mbox-dname txt-dname'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'mbox': 'mbox-dname',
            'txt': 'txt-dname',
        },
    ),
    (
        dns.rdata.from_text(
            dns.rdataclass.IN,
            dns.rdatatype.RRSIG,
            'SOA 5 2 3600 20101127004331 20101119213831 61695 dnspython.org. sDUlltRlFTQw5ITFxOXW3TgmrHeMeNpdqcZ4EXxM9FHhIlte6V9YCnDw'
            ' t6dvM9jAXdIEi03l9H/RAd9xNNW6gvGMHsBGzpvvqFQxIBR2PoiZA1mX /SWHZFdbt4xjYTtXqpyYvrMK0Dt7bUYPadyhPFCJ1B+I8Zi7B5WJEOd0 8vs=',
        ),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'type_covered': 'SOA',
            'algorithm': 5,
            'labels': 2,
            'original_ttl': 3600,
            'expiration': 1290818611,
            'inception': 1290202711,
            'key_tag': 61695,
            'signer': 'dnspython.org.',
            'signature': (
                'sDUlltRlFTQw5ITFxOXW3TgmrHeMeNpdqcZ4EXxM9FHhIlte6V9YCnDwt6dvM9jAXdIEi03l9H/RAd9xNNW6gv'
                'GMHsBGzpvvqFQxIBR2PoiZA1mX/SWHZFdbt4xjYTtXqpyYvrMK0Dt7bUYPadyhPFCJ1B+I8Zi7B5WJEOd08vs='
            ),
        },
    ),
    (
        dns.rdata.from_text(
            dns.rdataclass.IN,
            dns.rdatatype.RRSIG,
            'NSEC 1 3 3600 20200101000000 20030101000000 2143 foo. MxFcby9k/yvedMfQgKzhH5er0Mu/vILz'
            ' 45IkskceFGgiWCn/GxHhai6VAuHAoNUz 4YoU1tVfSCSqQYn6//11U6Nld80jEeC8 aTrO+KKmCaY=',
        ),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'type_covered': 'NSEC',
            'algorithm': 1,
            'labels': 3,
            'original_ttl': 3600,
            'expiration': 1577836800,
            'inception': 1041379200,
            'key_tag': 2143,
            'signer': 'foo.',
            'signature': 'MxFcby9k/yvedMfQgKzhH5er0Mu/vILz45IkskceFGgiWCn/GxHhai6VAuHAoNUz4YoU1tVfSCSqQYn6//11U6Nld80jEeC8aTrO+KKmCaY=',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, 'ns.example.com. ns.example.org. 1 7200 900 1209600 86400'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'mname': 'ns.example.com.',
            'rname': 'ns.example.org.',
            'serial': 1,
            'refresh': 7200,
            'retry': 900,
            'expire': 1209600,
            'minimum': 86400,
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SPF, '"v=spf1 a mx" " -all"'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'strings': [b'v=spf1 a mx', b' -all'],
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SPF, '"v=spf1 a mx" " -all"'),
        {'to_unicode': False, 'add_synthetic': True},
        {
            'strings': [b'v=spf1 a mx', b' -all'],
            'value': b'v=spf1 a mx -all',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SRV, r'0 1 443 exchange.example.com'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'priority': 0,
            'weight': 1,
            'port': 443,
            'target': 'exchange.example.com',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SSHFP, r'1 1 aa549bfe898489c02d1715d97d79c57ba2fa76ab'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'algorithm': 1,
            'fp_type': 1,
            'fingerprint': 'aa549bfe898489c02d1715d97d79c57ba2fa76ab',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TLSA, r'3 1 1 a9cdf989b504fe5dca90c0d2167b6550570734f7c763e09fdf88904e06157065'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'usage': 3,
            'selector': 1,
            'mtype': 1,
            'cert': 'a9cdf989b504fe5dca90c0d2167b6550570734f7c763e09fdf88904e06157065',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo bar"'),
        {'to_unicode': False, 'add_synthetic': False},
        {
            'strings': [b'asdf', b'foo bar'],
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo bar"'),
        {'to_unicode': False, 'add_synthetic': True},
        {
            'strings': [b'asdf', b'foo bar'],
            'value': b'asdffoo bar',
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo bar"'),
        {'to_unicode': True, 'add_synthetic': False},
        {
            'strings': [u'asdf', u'foo bar'],
        },
    ),
    (
        dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo bar"'),
        {'to_unicode': True, 'add_synthetic': True},
        {
            'strings': [u'asdf', u'foo bar'],
            'value': u'asdffoo bar',
        },
    ),
]


if dns.version.MAJOR >= 2:
    # https://github.com/rthalley/dnspython/issues/321 makes this not working on dnspython < 2.0.0,
    # which affects Python 3.5 and 2.x since these are only supported by dnspython < 2.0.0.
    TEST_CONVERT_RDATA_TO_DICT.extend([
        (
            dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo \195\164"'),
            {'to_unicode': False, 'add_synthetic': False},
            {
                'strings': [b'asdf', b'foo \xC3\xA4'],
            },
        ),
        (
            dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo \195\164"'),
            {'to_unicode': False, 'add_synthetic': True},
            {
                'strings': [b'asdf', b'foo \xC3\xA4'],
                'value': b'asdffoo \xC3\xA4',
            },
        ),
        (
            dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo \195\164"'),
            {'to_unicode': True, 'add_synthetic': False},
            {
                'strings': [u'asdf', u'foo ä'],
            },
        ),
        (
            dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.TXT, r'asdf "foo \195\164"'),
            {'to_unicode': True, 'add_synthetic': True},
            {
                'strings': [u'asdf', u'foo ä'],
                'value': u'asdffoo ä',
            },
        ),
    ])


@pytest.mark.parametrize("rdata, kwarg, expected_result", TEST_CONVERT_RDATA_TO_DICT)
def test_convert_rdata_to_dict(rdata, kwarg, expected_result):
    result = convert_rdata_to_dict(rdata, **kwarg)
    print(expected_result)
    print(result)
    assert expected_result == result


def test_error():
    v = RDTYPE_TO_FIELDS.pop(dns.rdatatype.A)
    try:
        with pytest.raises(ValueError) as exc:
            convert_rdata_to_dict(dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.A, '3.3.3.3'))
    finally:
        RDTYPE_TO_FIELDS[dns.rdatatype.A] = v
    print(exc.value.args)
    assert exc.value.args == ('Unsupported record type 1', )
