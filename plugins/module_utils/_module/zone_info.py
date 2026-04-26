# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import traceback
import typing as t

from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils._argspec import ArgumentSpec
from ansible_collections.community.dns.plugins.module_utils._zone_record_api import (
    DNSAPIAuthenticationError,
    DNSAPIError,
)

from ._utils import normalize_dns_name

if t.TYPE_CHECKING:
    from ansible.module_utils.basic import AnsibleModule  # pragma: no cover

    from .._provider import ProviderInformation  # pragma: no cover
    from .._zone_record_api import ZoneRecordAPI  # pragma: no cover
    from .._zone_record_set_api import ZoneRecordSetAPI  # pragma: no cover


def create_module_argument_spec(
    provider_information: ProviderInformation,
) -> ArgumentSpec:
    return ArgumentSpec(
        argument_spec={
            "zone_name": {"type": "str", "aliases": ["zone"]},
            "zone_id": {"type": provider_information.get_zone_id_type()},
        },
        required_one_of=[
            ("zone_name", "zone_id"),
        ],
        mutually_exclusive=[
            ("zone_name", "zone_id"),
        ],
    )


def run_module(
    module: AnsibleModule,
    create_api: t.Callable[[], ZoneRecordAPI | ZoneRecordSetAPI],
    provider_information: ProviderInformation,
) -> t.NoReturn:
    try:
        # Create API
        api = create_api()

        # Get zone information
        if module.params.get("zone_name") is not None:
            zone_id = normalize_dns_name(module.params.get("zone_name"))
            zone = api.get_zone_by_name(zone_id)
            if zone is None:
                module.fail_json(msg="Zone not found")
        else:
            zone = api.get_zone_by_id(module.params.get("zone_id"))
            if zone is None:
                module.fail_json(msg="Zone not found")

        module.exit_json(
            changed=False,
            zone_name=zone.name,
            zone_id=zone.id,
            zone_info=zone.info,
        )
    except DNSAPIAuthenticationError as e:
        module.fail_json(
            msg=f"Cannot authenticate: {e}",
            error=to_text(e),
            exception=traceback.format_exc(),
        )
    except DNSAPIError as e:
        module.fail_json(
            msg=f"Error: {e}",
            error=to_text(e),
            exception=traceback.format_exc(),
        )
