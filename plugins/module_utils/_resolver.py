# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import traceback
import typing as t

from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native, to_text

try:
    import dns
    import dns.exception
    import dns.inet
    import dns.message
    import dns.name
    import dns.query
    import dns.rcode
    import dns.rdatatype
    import dns.resolver
    import dns.version
except ImportError:
    DNSPYTHON_IMPORTERROR = traceback.format_exc()
else:
    DNSPYTHON_IMPORTERROR = None  # type: ignore  # TODO

if t.TYPE_CHECKING:
    from collections.abc import Collection, Mapping, Sequence  # pragma: no cover

    from ansible.module_utils.basic import AnsibleModule  # pragma: no cover

    _P = t.ParamSpec("_P")  # pragma: no cover
    _T = t.TypeVar("_T")  # pragma: no cover

    class ResolverParams(t.TypedDict):  # pragma: no cover
        search: t.NotRequired[bool]  # pragma: no cover


_EDNS_SIZE = 1232  # equals dns.message.DEFAULT_EDNS_PAYLOAD; larger values cause problems with Route53 nameservers for me


class ResolverError(Exception):
    pass


class InvalidInput(ResolverError):
    pass


class _Resolve:
    def __init__(
        self, timeout: float = 10, timeout_retries: int = 3, servfail_retries: int = 0
    ) -> None:
        self.timeout = timeout
        self.timeout_retries = timeout_retries
        self.servfail_retries = servfail_retries
        self.default_resolver = dns.resolver.get_default_resolver()

    def _handle_reponse_errors(
        self,
        target: dns.name.Name,
        response: dns.message.Message,
        nameserver: (
            Sequence[str | dns.nameserver.Nameserver]
            | str
            | dns.nameserver.Nameserver
            | None
        ) = None,
        query: str | None = None,
        accept_errors: Collection[dns.rcode.Rcode] | None = None,
    ):
        rcode = response.rcode()
        if rcode == dns.rcode.NOERROR:
            return True
        if accept_errors and rcode in accept_errors:
            return True
        if rcode == dns.rcode.NXDOMAIN:
            raise dns.resolver.NXDOMAIN(qnames=[target], responses={target: response})
        msg = f"Error {dns.rcode.to_text(rcode)}"
        if nameserver:
            msg = f"{msg} while querying {nameserver}"
        if query:
            msg = f"{msg} with query {query}"
        raise ResolverError(msg)

    def _handle_timeout(
        self, function: t.Callable[_P, _T], *args: _P.args, **kwargs: _P.kwargs
    ) -> _T:
        retry = 0
        while True:
            try:
                return function(*args, **kwargs)
            except dns.exception.Timeout as exc:
                if retry >= self.timeout_retries:
                    raise exc
                retry += 1

    def _resolve(
        self,
        resolver: dns.resolver.Resolver,
        dnsname: dns.name.Name,
        *,
        handle_response_errors: bool = False,
        rdtype: dns.rdatatype.RdataType,
        **kwargs: t.Unpack[ResolverParams],
    ) -> dns.rrset.RRset | None:
        retry = 0
        while True:
            response = self._handle_timeout(
                resolver.resolve,
                dnsname,
                lifetime=self.timeout,
                rdtype=rdtype,
                **kwargs,
            )
            if (
                response.response.rcode() == dns.rcode.SERVFAIL
                and retry < self.servfail_retries
            ):
                retry += 1
                continue
            if handle_response_errors:
                self._handle_reponse_errors(
                    dnsname, response.response, nameserver=resolver.nameservers
                )
            return response.rrset


class SimpleResolver(_Resolve):
    def __init__(
        self,
        timeout: float = 10,
        timeout_retries: int = 3,
        servfail_retries: int = 0,
    ) -> None:
        super().__init__(
            timeout=timeout,
            timeout_retries=timeout_retries,
            servfail_retries=servfail_retries,
        )

    def resolve(
        self,
        target: str,
        *,
        nxdomain_is_empty: bool = True,
        server_addresses=None,
        target_can_be_relative: bool = False,
        rdtype: dns.rdatatype.RdataType,
        **kwargs: t.Unpack[ResolverParams]
    ):
        dnsname = (
            dns.name.from_unicode(to_text(target), origin=None)
            if target_can_be_relative
            else dns.name.from_unicode(to_text(target))
        )

        resolver = self.default_resolver
        if server_addresses:
            resolver = dns.resolver.Resolver(configure=False)
            resolver.timeout = self.timeout
            resolver.nameservers = server_addresses

        resolver.use_edns(0, ednsflags=dns.flags.DO, payload=_EDNS_SIZE)

        try:
            return self._resolve(
                resolver, dnsname, handle_response_errors=True, rdtype=rdtype, **kwargs
            )
        except dns.resolver.NXDOMAIN:
            if nxdomain_is_empty:
                return None
            raise
        except dns.resolver.NoAnswer:
            return None

    def resolve_addresses(
        self, target: str | bytes, **kwargs: t.Unpack[ResolverParams]
    ) -> list[str]:
        dnsname = dns.name.from_unicode(to_text(target))
        resolver = self.default_resolver
        result = []
        try:
            for data in (
                self._resolve(
                    resolver,
                    dnsname,
                    handle_response_errors=True,
                    rdtype=dns.rdatatype.A,
                    **kwargs,
                )
                or ()
            ):
                result.append(str(data))
        except dns.resolver.NoAnswer:
            pass
        try:
            for data in (
                self._resolve(
                    resolver,
                    dnsname,
                    handle_response_errors=True,
                    rdtype=dns.rdatatype.AAAA,
                    **kwargs,
                )
                or ()
            ):
                result.append(str(data))
        except dns.resolver.NoAnswer:
            pass
        return result


class ResolveDirectlyFromNameServers(_Resolve):
    def __init__(
        self,
        timeout: float = 10,
        timeout_retries: int = 3,
        servfail_retries: int = 0,
        always_ask_default_resolver: bool = True,
        server_addresses: Sequence[str] | None = None,
    ) -> None:
        super().__init__(
            timeout=timeout,
            timeout_retries=timeout_retries,
            servfail_retries=servfail_retries,
        )
        self.cache: dict[tuple[str, t.Literal["ns", "addr"]], list[str]] = {}
        self.cname_cache: dict[str, dns.name.Name | None] = {}
        self.resolver_cache: dict[str, dns.resolver.Resolver] = {}
        self.default_nameservers: list[str | dns.nameserver.Nameserver] = list(
            self.default_resolver.nameservers
            if server_addresses is None
            else server_addresses
        )
        self.always_ask_default_resolver = always_ask_default_resolver

    def _lookup_ns_names(
        self,
        target: dns.name.Name,
        nameservers: Sequence[str] | None = None,
        nameserver_ips: Sequence[str | dns.nameserver.Nameserver] | None = None,
    ) -> tuple[list[str] | None, dns.name.Name | None]:
        if self.always_ask_default_resolver:
            nameservers = None
            nameserver_ips = self.default_nameservers
        if nameservers is None and nameserver_ips is None:
            nameserver_ips = self.default_nameservers
        if not nameserver_ips and nameservers:
            for ns in nameservers:
                nameserver_ips = self._lookup_address(ns)
                if nameserver_ips:
                    break
        if not nameserver_ips:
            if nameservers:
                raise ResolverError(
                    "Have neither nameservers nor nameserver IPs: the given nameservers do not resolve to IPs"
                )
            raise ResolverError("Have neither nameservers nor nameserver IPs")

        nameserver = nameserver_ips[0]

        # Sanity check: do we have a valid nameserver IP?
        if isinstance(nameserver, str):
            try:
                dns.inet.af_for_address(nameserver)
            except ValueError as exc:
                raise InvalidInput(
                    f"Invalid nameserver IP address {nameserver}"
                ) from exc

        query = dns.message.make_query(target, dns.rdatatype.NS)
        retry = 0
        while True:
            if isinstance(nameserver, str):
                response = self._handle_timeout(
                    dns.query.udp, query, nameserver, timeout=self.timeout
                )
            else:
                response = self._handle_timeout(
                    nameserver.query,
                    query,
                    timeout=self.timeout,
                    # The following are taken from the default arguments of
                    # dns.resolver.Resolver.resolve():
                    source=None,
                    source_port=0,
                    max_size=False,
                )
            if response.rcode() == dns.rcode.SERVFAIL and retry < self.servfail_retries:
                retry += 1
                continue
            break
        self._handle_reponse_errors(
            target,
            response,
            nameserver=nameserver,
            query=f'get NS for "{target}"',
            accept_errors=[dns.rcode.NXDOMAIN],
        )

        cname = None
        for rrset in response.answer:
            if rrset.rdtype == dns.rdatatype.CNAME:
                cname = dns.name.from_text(to_text(rrset[0]))

        new_nameservers: list[str] = []
        rrsets = list(response.authority)
        rrsets.extend(response.answer)
        for rrset in rrsets:
            if rrset.rdtype == dns.rdatatype.SOA:
                # We keep the current nameservers
                return None, cname
            if rrset.rdtype == dns.rdatatype.NS:
                new_nameservers.extend(str(ns_record.target) for ns_record in rrset)
        return sorted(set(new_nameservers)) if new_nameservers else None, cname

    def _lookup_address_impl(
        self, target: dns.name.Name, rdtype: dns.rdatatype.RdataType
    ) -> list[str]:
        try:
            answer = self._resolve(
                self.default_resolver,
                target,
                handle_response_errors=True,
                rdtype=rdtype,
            )
            return [str(res) for res in answer or ()]
        except dns.resolver.NoAnswer:
            return []

    def _lookup_address(self, target) -> list[str]:
        result = self.cache.get((target, "addr"))
        if result is None:
            result = self._lookup_address_impl(target, dns.rdatatype.A)
            result.extend(self._lookup_address_impl(target, dns.rdatatype.AAAA))
            self.cache[(target, "addr")] = result
        return result

    def _do_lookup_ns(self, target: dns.name.Name) -> list[str] | None:
        nameserver_ips: Sequence[str | dns.nameserver.Nameserver] | None = (
            self.default_nameservers
        )
        nameservers: list[str] | None = None
        for i in range(2, len(target.labels) + 1):
            target_part = target.split(i)[1]
            _nameservers = self.cache.get((str(target_part), "ns"))
            if _nameservers is None:
                nameserver_names, cname = self._lookup_ns_names(
                    target_part, nameservers=nameservers, nameserver_ips=nameserver_ips
                )
                if nameserver_names is not None:
                    nameservers = nameserver_names

                if nameservers is not None:
                    self.cache[(str(target_part), "ns")] = nameservers
                self.cname_cache[str(target_part)] = cname
            else:
                nameservers = _nameservers
            nameserver_ips = None

        return nameservers

    def _lookup_ns(self, target: dns.name.Name) -> list[str] | None:
        result = self.cache.get((str(target), "ns"))
        if result is None:
            result = self._do_lookup_ns(target)
            if result is not None:
                self.cache[(str(target), "ns")] = result
        return result

    def _get_resolver(
        self, dnsname: dns.name.Name, nameservers
    ) -> dns.resolver.Resolver:
        cache_index = "|".join([str(dnsname)] + sorted(nameservers))
        resolver = self.resolver_cache.get(cache_index)
        if resolver is None:
            resolver = dns.resolver.Resolver(configure=False)
            resolver.use_edns(0, ednsflags=dns.flags.DO, payload=_EDNS_SIZE)
            resolver.timeout = self.timeout
            nameserver_ips = set()
            for nameserver in nameservers:
                nameserver_ips.update(self._lookup_address(nameserver))
            resolver.nameservers = sorted(nameserver_ips)
            self.resolver_cache[cache_index] = resolver
        return resolver

    def resolve_nameservers(
        self, target: str | bytes, resolve_addresses: bool = False
    ) -> list[str]:
        nameservers = self._lookup_ns(dns.name.from_unicode(to_text(target)))
        if resolve_addresses:
            nameserver_ips = set()
            for nameserver in nameservers or []:
                nameserver_ips.update(self._lookup_address(nameserver))
            nameservers = list(nameserver_ips)
        return sorted(nameservers or [])

    def resolve(
        self,
        target: str | bytes,
        *,
        nxdomain_is_empty: bool = True,
        rdtype: dns.rdatatype.RdataType,
        **kwargs: t.Unpack[ResolverParams]
    ) -> dict[str, dns.rrset.RRset | None]:
        dnsname = dns.name.from_unicode(to_text(target))
        loop_catcher = set()
        while True:
            try:
                nameservers = self._lookup_ns(dnsname)
            except dns.resolver.NXDOMAIN:
                if nxdomain_is_empty:
                    return {}
                raise
            cname = self.cname_cache.get(str(dnsname))
            if cname is None:
                break
            dnsname = cname
            if dnsname in loop_catcher:
                raise ResolverError(f"Found CNAME loop starting at {to_native(target)}")
            loop_catcher.add(dnsname)

        results: dict[str, dns.rrset.RRset | None] = {}
        for nameserver in nameservers or []:
            results[nameserver] = None
            resolver = self._get_resolver(dnsname, [nameserver])
            try:
                results[nameserver] = self._resolve(
                    resolver,
                    dnsname,
                    handle_response_errors=True,
                    rdtype=rdtype,
                    **kwargs,
                )
            except dns.resolver.NoAnswer:
                pass
            except dns.resolver.NXDOMAIN:
                if nxdomain_is_empty:
                    # Note that rdclass is not always correct, but it's good enough for us...
                    results[nameserver] = dns.rrset.RRset(
                        name=dnsname, rdclass=dns.rdataclass.IN, rdtype=rdtype
                    )
                else:
                    raise
        return results


def guarded_run(
    runner: t.Callable[[], _T],
    module: AnsibleModule,
    *,
    server: str | None = None,
    generate_additional_results: t.Callable[[], Mapping[str, t.Any]] | None = None,
) -> _T:
    suffix = f" for {server}" if server is not None else ""
    kwargs: Mapping[str, t.Any] = {}
    try:
        return runner()
    except InvalidInput as e:
        if generate_additional_results is not None:
            kwargs = generate_additional_results()
        module.fail_json(
            msg=f"Invalid input{suffix}: {to_native(e)}",
            exception=traceback.format_exc(),
            **kwargs,
        )
    except ResolverError as e:
        if generate_additional_results is not None:
            kwargs = generate_additional_results()
        module.fail_json(
            msg=f"Unexpected resolving error{suffix}: {to_native(e)}",
            exception=traceback.format_exc(),
            **kwargs,
        )
    except dns.exception.DNSException as e:
        if generate_additional_results is not None:
            kwargs = generate_additional_results()
        module.fail_json(
            msg=f"Unexpected DNS error{suffix}: {to_native(e)}",
            exception=traceback.format_exc(),
            **kwargs,
        )


def assert_requirements_present(module: AnsibleModule) -> None:
    if DNSPYTHON_IMPORTERROR is not None:
        module.fail_json(
            msg=missing_required_lib("dnspython >= 2.0.0"),
            exception=DNSPYTHON_IMPORTERROR,
        )
    if dns.version.MAJOR < 2:
        module.fail_json(
            msg=missing_required_lib("dnspython >= 2.0.0")
            + f" Found version {dns.version.version}.",
            exception=DNSPYTHON_IMPORTERROR,
        )
