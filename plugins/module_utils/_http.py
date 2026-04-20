# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import abc
import typing
from urllib.error import HTTPError

from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.urls import (
    ConnectionError,  # noqa: A004
    NoSSLError,
    fetch_url,
    open_url,
)

if typing.TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule  # pragma: no cover


class NetworkError(Exception):
    pass


class HTTPHelper(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def fetch_url(
        self,
        url,  # type: str
        method="GET",  # type: str
        headers=None,  # type: dict[str, str] | None
        data=None,  # type: bytes | None
        timeout=None,  # type: int | None
    ):  # type: (...) -> tuple[bytes | None, dict[str, typing.Any]]
        """
        Execute a HTTP request and return a tuple (response_content, info).

        In case of errors, either raise NetworkError or terminate the program (for modules only!).
        """


class ModuleHTTPHelper(HTTPHelper):
    def __init__(
        self,
        module,  # type: AnsibleModule
    ):  # type: (...) -> None
        self.module = module  # type: AnsibleModule

    def fetch_url(
        self,
        url,  # type: str
        method="GET",  # type: str
        headers=None,  # type: dict[str, str] | None
        data=None,  # type: bytes | None
        timeout=None,  # type: int | None
    ):  # type: (...) -> tuple[bytes | None, dict[str, typing.Any]]
        response, info = fetch_url(
            self.module, url, method=method, headers=headers, data=data, timeout=timeout
        )
        try:
            # read() from a closed response returns ''
            if response.closed:
                raise TypeError
            content = response.read()
        except (AttributeError, TypeError):
            content = info.pop("body", None)
        return content, info


class OpenURLHelper(HTTPHelper):
    def fetch_url(
        self,
        url,  # type: str
        method="GET",  # type: str
        headers=None,  # type: dict[str, str] | None
        data=None,  # type: bytes | None
        timeout=None,  # type: int | None
    ):  # type: (...) -> tuple[bytes | None, dict[str, typing.Any]]
        info = {}
        try:
            req = open_url(
                url, method=method, headers=headers, data=data, timeout=timeout
            )
            result = req.read()
            info.update({k.lower(): v for k, v in req.info().items()})
            info["status"] = req.code
            info["url"] = req.geturl()
            req.close()
        except HTTPError as e:
            try:
                result = e.read()
            except AttributeError:
                result = ""
            try:
                info.update({k.lower(): v for k, v in e.info().items()})
            except Exception:  # pragma: no cover
                pass  # pragma: no cover
            info["status"] = e.code
        except NoSSLError as e:
            raise NetworkError("Cannot connect via SSL: {0}".format(to_native(e)))
        except (ConnectionError, ValueError) as e:
            raise NetworkError("Connection error: {0}".format(to_native(e)))

        return result, info
