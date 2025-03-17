# -*- coding: utf-8 -*-

# Copyright (c) 2015, Jan-Piet Mens <jpmens(at)gmail.com>
# Copyright (c) 2017 Ansible Project
# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function


__metaclass__ = type


import base64
import sys

from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text
from ansible.module_utils.six import binary_type


if sys.version_info >= (3, 6):
    import typing

    if typing.TYPE_CHECKING:
        import dns.rdatatype


NAME_TO_RDTYPE = {}  # type: dict[str, dns.rdatatype.RdataType]
RDTYPE_TO_NAME = {}  # type: dict[dns.rdatatype.RdataType, str]
RDTYPE_TO_FIELDS = {}  # type: dict[dns.rdatatype.RdataType, list[str]]

try:
    import dns.name
    import dns.rdata
    import dns.rdatatype
    import dns.rdtypes.ANY.NSEC3

    # The following data has been borrowed from community.general's dig lookup plugin.
    #
    # Note: adding support for RRSIG is hard work. :)
    for _name, _rdtype, _fields in [
        ('A', dns.rdatatype.A, ['address']),
        ('AAAA', dns.rdatatype.AAAA, ['address']),
        ('CAA', dns.rdatatype.CAA, ['flags', 'tag', 'value']),
        ('CNAME', dns.rdatatype.CNAME, ['target']),
        ('DNAME', dns.rdatatype.DNAME, ['target']),
        ('DNSKEY', dns.rdatatype.DNSKEY, ['flags', 'algorithm', 'protocol', 'key']),
        ('DS', dns.rdatatype.DS, ['algorithm', 'digest_type', 'key_tag', 'digest']),
        ('HINFO', dns.rdatatype.HINFO, ['cpu', 'os']),
        ('LOC', dns.rdatatype.LOC, ['latitude', 'longitude', 'altitude', 'size', 'horizontal_precision', 'vertical_precision']),
        ('MX', dns.rdatatype.MX, ['preference', 'exchange']),
        ('NAPTR', dns.rdatatype.NAPTR, ['order', 'preference', 'flags', 'service', 'regexp', 'replacement']),
        ('NS', dns.rdatatype.NS, ['target']),
        ('NSEC', dns.rdatatype.NSEC, ['next', 'windows']),
        ('NSEC3', dns.rdatatype.NSEC3, ['algorithm', 'flags', 'iterations', 'salt', 'next', 'windows']),
        ('NSEC3PARAM', dns.rdatatype.NSEC3PARAM, ['algorithm', 'flags', 'iterations', 'salt']),
        ('PTR', dns.rdatatype.PTR, ['target']),
        ('RP', dns.rdatatype.RP, ['mbox', 'txt']),
        ('RRSIG', dns.rdatatype.RRSIG, ['type_covered', 'algorithm', 'labels', 'original_ttl', 'expiration', 'inception', 'key_tag', 'signer', 'signature']),
        ('SOA', dns.rdatatype.SOA, ['mname', 'rname', 'serial', 'refresh', 'retry', 'expire', 'minimum']),
        ('SPF', dns.rdatatype.SPF, ['strings']),
        ('SRV', dns.rdatatype.SRV, ['priority', 'weight', 'port', 'target']),
        ('SSHFP', dns.rdatatype.SSHFP, ['algorithm', 'fp_type', 'fingerprint']),
        ('TLSA', dns.rdatatype.TLSA, ['usage', 'selector', 'mtype', 'cert']),
        ('TXT', dns.rdatatype.TXT, ['strings']),
    ]:
        NAME_TO_RDTYPE[_name] = _rdtype
        RDTYPE_TO_NAME[_rdtype] = _name
        RDTYPE_TO_FIELDS[_rdtype] = _fields

except ImportError:
    pass  # has to be handled on application level


def convert_rdata_to_dict(
    rdata,  # type: dns.rdata.Rdata
    to_unicode=True,  # type: bool
    add_synthetic=True,  # type: bool
):  # type: (...) -> dict[str, typing.Any]
    '''
    Convert a DNSPython record data object to a Python dictionary.

    Code borrowed from community.general's dig looup plugin.

    If ``to_unicode=True``, all strings will be converted to Unicode/UTF-8 strings.

    If ``add_synthetic=True``, for some record types additional fields are added.
    For TXT and SPF records, ``value`` contains the concatenated strings, for example.
    '''
    result = {}  # type: dict[str, typing.Any]

    fields = RDTYPE_TO_FIELDS.get(rdata.rdtype)
    if fields is None:
        raise ValueError('Unsupported record type {rdtype}'.format(rdtype=rdata.rdtype))
    for f in fields:
        val = getattr(rdata, f)

        if isinstance(val, dns.name.Name):
            val = dns.name.Name.to_text(val)

        if rdata.rdtype == dns.rdatatype.DS and f == 'digest':
            val = dns.rdata._hexify(rdata.digest).replace(' ', '')  # type: ignore
        if rdata.rdtype == dns.rdatatype.DNSKEY and f == 'algorithm':
            val = int(val)
        if rdata.rdtype == dns.rdatatype.DNSKEY and f == 'key':
            val = dns.rdata._base64ify(rdata.key).replace(' ', '')  # type: ignore
        if rdata.rdtype == dns.rdatatype.NSEC3 and f == 'next':
            val = to_native(base64.b32encode(rdata.next).translate(dns.rdtypes.ANY.NSEC3.b32_normal_to_hex).lower())  # type: ignore
        if rdata.rdtype in (dns.rdatatype.NSEC, dns.rdatatype.NSEC3) and f == 'windows':
            try:
                val = dns.rdtypes.util.Bitmap(rdata.windows).to_text().lstrip(' ')  # type: ignore
            except AttributeError:
                # dnspython < 2.0.0
                val = []
                for window, bitmap in rdata.windows:  # type: ignore
                    for i, byte in enumerate(bitmap):
                        for j in range(8):
                            if (byte >> (7 - j)) & 1 != 0:
                                val.append(dns.rdatatype.to_text(window * 256 + i * 8 + j))
                val = ' '.join(val).lstrip(' ')
        if rdata.rdtype in (dns.rdatatype.NSEC3, dns.rdatatype.NSEC3PARAM) and f == 'salt':
            val = dns.rdata._hexify(rdata.salt).replace(' ', '')  # type: ignore
        if rdata.rdtype == dns.rdatatype.RRSIG and f == 'type_covered':
            val = RDTYPE_TO_NAME.get(rdata.type_covered) or str(val)  # type: ignore
        if rdata.rdtype == dns.rdatatype.RRSIG and f == 'algorithm':
            val = int(val)
        if rdata.rdtype == dns.rdatatype.RRSIG and f == 'signature':
            val = dns.rdata._base64ify(rdata.signature).replace(' ', '')  # type: ignore
        if rdata.rdtype == dns.rdatatype.SSHFP and f == 'fingerprint':
            val = dns.rdata._hexify(rdata.fingerprint).replace(' ', '')  # type: ignore
        if rdata.rdtype == dns.rdatatype.TLSA and f == 'cert':
            val = dns.rdata._hexify(rdata.cert).replace(' ', '')  # type: ignore

        if isinstance(val, (list, tuple)):
            if to_unicode:
                val = [to_text(v) if isinstance(v, binary_type) else v for v in val]
            else:
                val = list(val)
        elif to_unicode and isinstance(val, binary_type):
            val = to_text(val)

        result[f] = val

    if add_synthetic:
        if rdata.rdtype in (dns.rdatatype.TXT, dns.rdatatype.SPF):
            if to_unicode:
                result['value'] = u''.join([to_text(str) for str in rdata.strings])  # type: ignore
            else:
                result['value'] = b''.join([to_bytes(str) for str in rdata.strings])  # type: ignore
    return result
