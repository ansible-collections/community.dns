# Copyright (c) 2025 Markus Bergholz
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import json
import typing as t
from urllib.error import HTTPError

from ansible.module_utils.urls import Request

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec

if t.TYPE_CHECKING:

    class FailJson:  # pragma: no cover
        def __call__(self, **kwargs) -> t.NoReturn: ...  # pragma: no cover


def create_adguardhome_argument_spec() -> ArgumentSpec:
    argument_spec = {
        "username": {"type": "str", "required": True},
        "password": {"type": "str", "required": True, "no_log": True},
        "host": {"type": "str", "required": True},
        "validate_certs": {"type": "bool", "default": True},
    }
    return ArgumentSpec(argument_spec=argument_spec)


class AdGuardHomeAPIHandler:
    def __init__(self, params: dict[str, t.Any], fail_json: FailJson) -> None:
        host: str = params["host"]  # type: ignore
        self.url = f"{host}/control/rewrite"

        self.validate_certs: bool = params["validate_certs"]  # type: ignore
        self.fail_json = fail_json
        self.r = Request(
            validate_certs=self.validate_certs,
            url_username=params["username"],
            url_password=params["password"],
            force_basic_auth=True,
            headers={"Content-Type": "application/json"},
        )

    def list(self) -> list[dict[str, t.Any]]:
        try:
            response = self.r.open("GET", f"{self.url}/list")

            return json.loads(response.read().decode("utf-8"))

        except HTTPError as e:
            self.fail_json(msg=e.read())

    def add_or_delete(
        self,
        domain: str,
        answer: str,
        method: t.Literal["add", "delete"],
        target: dict[str, t.Any],
    ) -> t.Literal[True]:
        """
        the delete api requires the matching answer value.
        but because we make the answer value optional, it's
        taken from previous `find_and_compare` function.
        """
        if method == "add":  # noqa: SIM108
            answer_value = answer
        else:
            answer_value = target["answer"] if answer is None else answer

        data = json.dumps({"domain": domain, "answer": answer_value}).encode("utf-8")
        try:
            self.r.open(
                "POST",
                f"{self.url}/{method}",
                data=data,
            )
            return True

        except HTTPError as e:
            self.fail_json(msg=e.read())

    def update(
        self, domain: str, answer: str, target: dict[str, t.Any]
    ) -> t.Literal[True]:
        data = json.dumps(
            {"target": target, "update": {"domain": domain, "answer": answer}}
        ).encode("utf-8")
        try:
            self.r.open(
                "PUT",
                f"{self.url}/update",
                data=data,
            )
            return True

        except HTTPError as e:
            self.fail_json(msg=e.read())
