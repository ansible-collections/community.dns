# Copyright (c) 2015, Jan-Piet Mens <jpmens(at)gmail.com>
# Copyright (c) 2017 Ansible Project
# Copyright (c) 2022, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import base64
import typing as t

from ansible.module_utils.common.text.converters import to_bytes, to_native, to_text

if t.TYPE_CHECKING:
    import dns.rdatatype  # pragma: no cover


NAME_TO_RDTYPE: dict[str, dns.rdatatype.RdataType] = {}
NAME_TO_REQUIRED_VERSION: dict[str, str] = {}
RDTYPE_TO_NAME: dict[dns.rdatatype.RdataType, str] = {}
RDTYPE_TO_FIELDS: dict[dns.rdatatype.RdataType, list[str]] = {}

try:
    import dns.name
    import dns.rdata
    import dns.rdatatype

    try:
        import dns.rdtypes.ANY.NSEC3
    except ImportError:  # pragma: no cover
        pass  # pragma: no cover
    try:
        import dns.rdtypes.svcbbase
    except ImportError:
        pass

    _HTTPS = getattr(dns.rdatatype, "HTTPS", None)
    _SVCB = getattr(dns.rdatatype, "SVCB", None)

    # The following data has been borrowed from community.general's dig lookup plugin.
    #
    # Note: adding support for RRSIG is hard work. :)
    for _name, _rdtype, _min_version, _fields in [
        ("A", dns.rdatatype.A, None, ["address"]),
        ("AAAA", dns.rdatatype.AAAA, None, ["address"]),
        ("CAA", dns.rdatatype.CAA, None, ["flags", "tag", "value"]),
        ("CNAME", dns.rdatatype.CNAME, None, ["target"]),
        ("DNAME", dns.rdatatype.DNAME, None, ["target"]),
        (
            "DNSKEY",
            dns.rdatatype.DNSKEY,
            None,
            ["flags", "algorithm", "protocol", "key"],
        ),
        (
            "DS",
            dns.rdatatype.DS,
            None,
            ["algorithm", "digest_type", "key_tag", "digest"],
        ),
        ("HINFO", dns.rdatatype.HINFO, None, ["cpu", "os"]),
        ("HTTPS", _HTTPS, "2.2.0", ["priority", "target", "params"]),
        (
            "LOC",
            dns.rdatatype.LOC,
            None,
            [
                "latitude",
                "longitude",
                "altitude",
                "size",
                "horizontal_precision",
                "vertical_precision",
            ],
        ),
        ("MX", dns.rdatatype.MX, None, ["preference", "exchange"]),
        (
            "NAPTR",
            dns.rdatatype.NAPTR,
            None,
            ["order", "preference", "flags", "service", "regexp", "replacement"],
        ),
        ("NS", dns.rdatatype.NS, None, ["target"]),
        ("NSEC", dns.rdatatype.NSEC, None, ["next", "windows"]),
        (
            "NSEC3",
            dns.rdatatype.NSEC3,
            None,
            ["algorithm", "flags", "iterations", "salt", "next", "windows"],
        ),
        (
            "NSEC3PARAM",
            dns.rdatatype.NSEC3PARAM,
            None,
            ["algorithm", "flags", "iterations", "salt"],
        ),
        ("PTR", dns.rdatatype.PTR, None, ["target"]),
        ("RP", dns.rdatatype.RP, None, ["mbox", "txt"]),
        (
            "RRSIG",
            dns.rdatatype.RRSIG,
            None,
            [
                "type_covered",
                "algorithm",
                "labels",
                "original_ttl",
                "expiration",
                "inception",
                "key_tag",
                "signer",
                "signature",
            ],
        ),
        (
            "SOA",
            dns.rdatatype.SOA,
            None,
            ["mname", "rname", "serial", "refresh", "retry", "expire", "minimum"],
        ),
        ("SPF", dns.rdatatype.SPF, None, ["strings"]),
        ("SRV", dns.rdatatype.SRV, None, ["priority", "weight", "port", "target"]),
        ("SSHFP", dns.rdatatype.SSHFP, None, ["algorithm", "fp_type", "fingerprint"]),
        ("SVCB", _SVCB, "2.2.0", ["priority", "target", "params"]),
        ("TLSA", dns.rdatatype.TLSA, None, ["usage", "selector", "mtype", "cert"]),
        ("TXT", dns.rdatatype.TXT, None, ["strings"]),
    ]:
        if _rdtype is None:
            if _min_version is None:  # pragma: no cover
                raise RuntimeError(
                    f"Internal error: rdtype {_name} is None, but min_version is also None!"
                )  # pragma: no cover
            NAME_TO_REQUIRED_VERSION[_name] = _min_version
        else:
            NAME_TO_RDTYPE[_name] = _rdtype
            RDTYPE_TO_NAME[_rdtype] = _name
            RDTYPE_TO_FIELDS[_rdtype] = _fields

except ImportError:
    pass  # has to be handled on application level


def _convert_dns_rdtypes_svcbbase_param(
    value: dns.rdtypes.svcbbase.Param,
) -> tuple[t.Any, bool]:
    if value is None:
        return None, False
    if isinstance(value, dns.rdtypes.svcbbase.GenericParam):
        return to_native(base64.b64encode(value.value)), True
    if isinstance(value, dns.rdtypes.svcbbase.MandatoryParam):
        return [dns.rdtypes.svcbbase.key_to_text(k) for k in value.keys], False
    if isinstance(value, dns.rdtypes.svcbbase.ALPNParam):
        return [
            to_native(base64.b64encode(identifier)) for identifier in value.ids
        ], True
    if isinstance(value, dns.rdtypes.svcbbase.PortParam):
        return value.port, False
    if isinstance(value, dns.rdtypes.svcbbase.IPv4HintParam):
        return [to_native(v) for v in value.addresses], False
    if isinstance(value, dns.rdtypes.svcbbase.IPv6HintParam):
        return [to_native(v) for v in value.addresses], False
    if isinstance(value, dns.rdtypes.svcbbase.ECHParam):
        return to_native(base64.b64encode(value.ech)), True
    # Fallbacks:
    if hasattr(value, "to_text"):  # pragma: no cover
        return value.to_text(), False  # pragma: no cover
    return str(value), False  # pragma: no cover


def convert_rdata_to_dict(
    rdata: dns.rdata.Rdata,
    to_unicode: bool = True,
    add_synthetic: bool = True,
) -> dict[str, t.Any]:
    """
    Convert a DNSPython record data object to a Python dictionary.

    Code borrowed from community.general's dig looup plugin.

    If ``to_unicode=True``, all strings will be converted to Unicode/UTF-8 strings.

    If ``add_synthetic=True``, for some record types additional fields are added.
    For TXT and SPF records, ``value`` contains the concatenated strings, for example.
    """
    result: dict[str, t.Any] = {}

    fields = RDTYPE_TO_FIELDS.get(rdata.rdtype)
    if fields is None:
        raise ValueError(f"Unsupported record type {rdata.rdtype}")
    for f in fields:
        val = getattr(rdata, f)

        if isinstance(val, dns.name.Name):
            val = dns.name.Name.to_text(val)

        if rdata.rdtype == dns.rdatatype.DS and f == "digest":
            val = dns.rdata._hexify(rdata.digest).replace(" ", "")  # type: ignore
        if rdata.rdtype == dns.rdatatype.DNSKEY and f == "algorithm":
            val = int(val)
        if rdata.rdtype == dns.rdatatype.DNSKEY and f == "key":
            val = dns.rdata._base64ify(rdata.key).replace(" ", "")  # type: ignore
        if rdata.rdtype == dns.rdatatype.NSEC3 and f == "next":
            val = to_native(base64.b32encode(rdata.next).translate(dns.rdtypes.ANY.NSEC3.b32_normal_to_hex).lower())  # type: ignore
        if rdata.rdtype in (dns.rdatatype.NSEC, dns.rdatatype.NSEC3) and f == "windows":
            val = dns.rdtypes.util.Bitmap(rdata.windows).to_text().lstrip(" ")  # type: ignore
        if (
            rdata.rdtype in (dns.rdatatype.NSEC3, dns.rdatatype.NSEC3PARAM)
            and f == "salt"
        ):
            val = dns.rdata._hexify(rdata.salt).replace(" ", "")  # type: ignore
        if rdata.rdtype == dns.rdatatype.RRSIG and f == "type_covered":
            val = RDTYPE_TO_NAME.get(rdata.type_covered) or str(val)  # type: ignore
        if rdata.rdtype == dns.rdatatype.RRSIG and f == "algorithm":
            val = int(val)
        if rdata.rdtype == dns.rdatatype.RRSIG and f == "signature":
            val = dns.rdata._base64ify(rdata.signature).replace(" ", "")  # type: ignore
        if rdata.rdtype == dns.rdatatype.SSHFP and f == "fingerprint":
            val = dns.rdata._hexify(rdata.fingerprint).replace(" ", "")  # type: ignore
        if rdata.rdtype == dns.rdatatype.TLSA and f == "cert":
            val = dns.rdata._hexify(rdata.cert).replace(" ", "")  # type: ignore
        if rdata.rdtype in (_HTTPS, _SVCB) and f == "params":
            val_res = {}
            for k, v in val.items():
                kk = dns.rdtypes.svcbbase.key_to_text(k)
                vv, _b64 = _convert_dns_rdtypes_svcbbase_param(v)
                val_res[kk] = vv
                # Not sure whether we want to include that:
                # if _b64:
                #     val_res[kk + "_encoded"] = v.to_text()
            val = val_res

        if isinstance(val, (list, tuple)):
            val = (
                [to_text(v) if isinstance(v, bytes) else v for v in val]
                if to_unicode
                else list(val)
            )
        elif to_unicode and isinstance(val, bytes):
            val = to_text(val)

        result[f] = val

    if add_synthetic:  # noqa: SIM102
        if rdata.rdtype in (dns.rdatatype.TXT, dns.rdatatype.SPF):
            if to_unicode:
                result["value"] = "".join([to_text(value) for value in rdata.strings])  # type: ignore
            else:
                result["value"] = b"".join([to_bytes(value) for value in rdata.strings])  # type: ignore
    return result
