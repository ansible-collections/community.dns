# Copyright (c) 2021 Felix Fontein
# Copyright (c) 2020 Markus Bergholz <markuman+spambelongstogoogle@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import json
import time
import typing as t
from urllib.parse import urlencode

from ansible.module_utils.common.text.converters import to_native

from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    DNSAPIAuthenticationError,
    DNSAPIError,
)

if t.TYPE_CHECKING:
    from collections.abc import Collection  # pragma: no cover

    from ._http import HTTPHelper  # pragma: no cover
    from ._provider import ProviderInformation  # pragma: no cover
    from ._record import DNSRecord  # pragma: no cover
    from ._zone_record_api import ZoneRecordAPI  # pragma: no cover


ERROR_CODES = {
    200: "Successful response",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    406: "Not acceptable",
    409: "Conflict",
    422: "Unprocessable entity",
    500: "Internal Server Error",
}
UNKNOWN_ERROR = "Unknown Error"


def _get_header_value(
    info: dict[str, t.Any],
    header_name: str,
) -> str | None:
    header_name = header_name.lower()
    header_value = info.get(header_name)
    for k, v in info.items():
        if k.lower() == header_name:
            header_value = v
    return header_value


class JSONAPIHelper:
    def __init__(
        self,
        http_helper: HTTPHelper,
        token: str,
        api: str,
        debug: bool = False,
    ) -> None:
        """
        Create a new JSON API helper instance with given API key.
        """
        self._api = api
        self._http_helper = http_helper
        self._token = token
        self._debug = debug

    def _build_url(
        self,
        url: str,
        query: dict[str, str] | None = None,
    ) -> str:
        return f"{self._api}{url}{'?' + urlencode(query) if query else ''}"

    def _extract_error_message(
        self,
        result: bytes | None,
    ) -> str:
        if result is None:
            return ""
        return f" with data: {result!r}"

    def _validate(
        self,
        result: bytes | None = None,
        info: dict[str, t.Any] | None = None,
        expected: Collection[int] | None = None,
        method: str = "GET",
    ) -> None:
        if info is None:
            raise DNSAPIError("Internal error: info needs to be provided")
        status = info["status"]
        url = info.get("url")  # not present when using open_url
        # Check expected status
        error_code = ERROR_CODES.get(status, UNKNOWN_ERROR)
        if expected is not None:
            if status not in expected:
                more = self._extract_error_message(result)
                statuses = ", ".join([f"{e}" for e in expected])
                raise DNSAPIError(
                    f"Expected HTTP status {statuses} for {method} {url}, but got HTTP status {status} ({error_code}){more}"
                )
        else:
            if status < 200 or status >= 300:
                more = self._extract_error_message(result)
                raise DNSAPIError(
                    f"Expected successful HTTP status for {method} {url}, but got HTTP status {status} ({error_code}){more}"
                )

    def _process_json_result(
        self,
        content: bytes | None,
        info: dict[str, t.Any],
        must_have_content: bool | list[int] | tuple[int, ...] = True,
        method: str = "GET",
        expected: Collection[int] | None = None,
    ) -> tuple[dict[str, t.Any] | list[t.Any] | None, dict[str, t.Any]]:
        if isinstance(must_have_content, (list, tuple)):
            must_have_content = info["status"] in must_have_content
        # Check for unauthenticated
        if info["status"] == 401:
            message = "Unauthorized: the authentication parameters are incorrect (HTTP status 401)"
            try:
                body = json.loads(content.decode("utf8"))  # type: ignore
                if body["message"]:
                    message = f"{message}: {body['message']}"
            except Exception:
                pass
            raise DNSAPIAuthenticationError(message)
        if info["status"] == 403:
            message = (
                "Forbidden: you do not have access to this resource (HTTP status 403)"
            )
            try:
                body = json.loads(content.decode("utf8"))  # type: ignore
                if body["message"]:
                    message = f"{message}: {body['message']}"
            except Exception:
                pass
            raise DNSAPIAuthenticationError(message)
        # Check Content-Type header
        content_type = _get_header_value(info, "content-type")
        if content_type != "application/json" and (
            content_type is None or not content_type.startswith("application/json;")
        ):
            if must_have_content:
                raise DNSAPIError(
                    f"{method} {info['url']} did not yield JSON data, but HTTP status code {info['status']}"
                    f' with Content-Type "{content_type}" and data: {to_native(content)}'
                )
            self._validate(result=content, info=info, expected=expected, method=method)
            return None, info
        # Decode content as JSON
        try:
            result = json.loads(content.decode("utf8"))  # type: ignore
        except Exception:
            if must_have_content:
                raise DNSAPIError(
                    f"{method} {info['url']} did not yield JSON data, but HTTP status code {info['status']} with data: {to_native(content)}"
                )
            self._validate(result=content, info=info, expected=expected, method=method)
            return None, info
        self._validate(result=result, info=info, expected=expected, method=method)
        return result, info

    def _is_rate_limiting_result(self, content, info):
        if info["status"] != 429:
            return False
        try:
            return max(min(float(_get_header_value(info, "retry-after")), 60), 1)  # type: ignore
        except (ValueError, TypeError):
            return 10

    def _should_retry(self, content, info):
        return info["status"] in (-1, 502, 503, 504)

    def _request(self, url: str, **kwargs) -> tuple[bytes | None, dict[str, t.Any]]:
        """Execute a HTTP request and handle common things like rate limiting."""
        number_retries = 10
        countdown = number_retries + 1
        cause = ""
        while True:
            content, info = self._http_helper.fetch_url(url, **kwargs)
            countdown -= 1
            retry_wait = None
            if self._should_retry(content, info):
                retry_wait = 0.5
                cause = (
                    "a local HTTP request error"
                    if info["status"] == -1
                    else f"HTTP status {info['status']}"
                )
            else:
                retry_after = self._is_rate_limiting_result(content, info)
                if retry_after is not False:
                    cause = "429 Too Many Attempts"
                    retry_wait = 10 if retry_after is True else retry_after
            if retry_wait is not None:
                if countdown <= 0:
                    break
                time.sleep(retry_wait)
                continue
            return content, info
        raise DNSAPIError(
            f"Stopping after {number_retries} failed retries with {cause}"
        )

    def _create_headers(self) -> dict[str, str]:
        return {
            "accept": "application/json",
        }

    def _create_post_headers(self) -> dict[str, str]:
        return self._create_headers()

    def _create_put_headers(self) -> dict[str, str]:
        return self._create_headers()

    def _get(
        self,
        url: str,
        query: dict[str, str] | None = None,
        must_have_content: bool | list[int] | tuple[int, ...] = True,
        expected: Collection[int] | None = None,
    ) -> tuple[dict[str, t.Any] | list[t.Any] | None, dict[str, t.Any]]:
        full_url = self._build_url(url, query)
        if self._debug:
            pass  # pragma: no cover
            # q.q('Request: GET {0}'.format(full_url))
        headers = self._create_headers()
        content, info = self._request(full_url, headers=headers, method="GET")
        return self._process_json_result(
            content,
            info,
            must_have_content=must_have_content,
            method="GET",
            expected=expected,
        )

    def _post(
        self,
        url: str,
        data: dict[str, t.Any] | None = None,
        query: dict[str, str] | None = None,
        must_have_content: bool | list[int] | tuple[int, ...] = True,
        expected: Collection[int] | None = None,
    ) -> tuple[dict[str, t.Any] | list[t.Any] | None, dict[str, t.Any]]:
        full_url = self._build_url(url, query)
        if self._debug:
            pass  # pragma: no cover
            # q.q('Request: POST {0}'.format(full_url))
        headers = self._create_post_headers()
        encoded_data = None
        if data is not None:
            headers["content-type"] = "application/json"
            encoded_data = json.dumps(data).encode("utf-8")
        content, info = self._request(
            full_url, headers=headers, method="POST", data=encoded_data
        )
        return self._process_json_result(
            content,
            info,
            must_have_content=must_have_content,
            method="POST",
            expected=expected,
        )

    def _put(
        self,
        url: str,
        data: dict[str, t.Any] | None = None,
        query: dict[str, str] | None = None,
        must_have_content: bool | list[int] | tuple[int, ...] = True,
        expected: Collection[int] | None = None,
    ) -> tuple[dict[str, t.Any] | list[t.Any] | None, dict[str, t.Any]]:
        full_url = self._build_url(url, query)
        if self._debug:
            pass  # pragma: no cover
            # q.q('Request: PUT {0}'.format(full_url))
        headers = self._create_put_headers()
        encoded_data = None
        if data is not None:
            headers["content-type"] = "application/json"
            encoded_data = json.dumps(data).encode("utf-8")
        content, info = self._request(
            full_url, headers=headers, method="PUT", data=encoded_data
        )
        return self._process_json_result(
            content,
            info,
            must_have_content=must_have_content,
            method="PUT",
            expected=expected,
        )

    def _delete(
        self,
        url: str,
        query: dict[str, str] | None = None,
        must_have_content: bool | list[int] | tuple[int, ...] = True,
        expected: Collection[int] | None = None,
    ) -> tuple[dict[str, t.Any] | list[t.Any] | None, dict[str, t.Any]]:
        full_url = self._build_url(url, query)
        if self._debug:
            pass  # pragma: no cover
            # q.q('Request: DELETE {0}'.format(full_url))
        headers = self._create_headers()
        content, info = self._request(full_url, headers=headers, method="DELETE")
        return self._process_json_result(
            content,
            info,
            must_have_content=must_have_content,
            method="DELETE",
            expected=expected,
        )
