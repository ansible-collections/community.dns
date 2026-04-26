# Copyright (c) 2023, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this plugin util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t
from collections.abc import Callable

from ansible.errors import AnsibleError
from ansible.module_utils.basic import missing_required_lib
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.dns.plugins.module_utils._resolver import (
    ResolverError,
)

DNSPYTHON_IMPORTERROR: ImportError | None
try:
    import dns  # pylint: disable=unused-import
    import dns.exception  # pylint: disable=unused-import
    import dns.message  # pylint: disable=unused-import
    import dns.name  # pylint: disable=unused-import
    import dns.query  # pylint: disable=unused-import
    import dns.rcode  # pylint: disable=unused-import
    import dns.rdatatype  # pylint: disable=unused-import
    import dns.resolver  # pylint: disable=unused-import
    import dns.version
except ImportError as exc:
    DNSPYTHON_IMPORTERROR = exc
else:
    DNSPYTHON_IMPORTERROR = None  # type: ignore  # TODO

if t.TYPE_CHECKING:
    _T = t.TypeVar("_T")


def guarded_run(
    runner: Callable[[], _T],
    error_class: type[Exception] = AnsibleError,
    server: str | None = None,
) -> _T:
    suffix = f" for {server}" if server is not None else ""
    try:
        return runner()
    except ResolverError as e:
        raise error_class(f"Unexpected resolving error{suffix}: {to_native(e)}") from e
    except dns.exception.DNSException as e:
        raise error_class(f"Unexpected DNS error{suffix}: {to_native(e)}") from e


def assert_requirements_present(plugin_name: str, plugin_type: str) -> None:
    if DNSPYTHON_IMPORTERROR is not None:
        msg = f'The {plugin_name} {plugin_type} plugin is missing requirements: {missing_required_lib("dnspython >= 2.0.0")}'
        raise AnsibleError(msg) from DNSPYTHON_IMPORTERROR
    if dns.version.MAJOR < 2:
        msg = (
            f'The {plugin_name} {plugin_type} plugin is missing requirements: {missing_required_lib("dnspython >= 2.0.0")}.'
            f" Found version {dns.version.version}."
        )
        raise AnsibleError(msg)
