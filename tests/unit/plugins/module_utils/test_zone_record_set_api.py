# -*- coding: utf-8 -*-
# Copyright (c) 2021, Felix Fontein <felix@fontein.de>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# pylint: disable=use-implicit-booleaness-not-comparison

# Make coding more python3-ish
from __future__ import absolute_import, division, print_function


__metaclass__ = type


from ansible_collections.community.dns.plugins.module_utils.record_set import (
    DNSRecordSet,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_api import (
    NOT_PROVIDED,
    DNSAPIError,
)
from ansible_collections.community.dns.plugins.module_utils.zone_record_set_api import (
    ZoneRecordSetAPI,
)


class _TestZoneRecordSetAPI(ZoneRecordSetAPI):
    def __init__(self):
        self.commands = []
        self.add_record_set_return_values = []
        self.update_record_set_return_values = []
        self.delete_record_set_return_values = []

    def assert_done(self):
        assert len(self.add_record_set_return_values) == 0
        assert len(self.update_record_set_return_values) == 0
        assert len(self.delete_record_set_return_values) == 0

    def get_zone_by_name(self, name):
        raise NotImplementedError()

    def get_zone_by_id(self, zone_id):
        raise NotImplementedError()

    def get_zone_record_sets(self, zone_id, prefix=NOT_PROVIDED, record_type=NOT_PROVIDED):
        raise NotImplementedError()

    def add_record_set(self, zone_id, record_set):
        self.commands.append(("add_record_set", zone_id, record_set))
        res = self.add_record_set_return_values.pop(0)
        if isinstance(res, DNSAPIError):
            raise res
        return res

    def update_record_set(self, zone_id, record_set, updated_records=True, updated_ttl=True):
        self.commands.append(("update_record_set", zone_id, record_set, updated_records, updated_ttl))
        res = self.update_record_set_return_values.pop(0)
        if isinstance(res, DNSAPIError):
            raise res
        return res

    def delete_record_set(self, zone_id, record_set):
        self.commands.append(("delete_record_set", zone_id, record_set))
        res = self.delete_record_set_return_values.pop(0)
        if isinstance(res, DNSAPIError):
            raise res
        return res


def test_add_record_sets():
    a1 = DNSRecordSet()
    a1.id = "a1"
    a2 = DNSRecordSet()
    a2.id = "a2"

    a1res = DNSRecordSet()
    a1res.id = "a1res"
    a2res = DNSRecordSet()
    a2res.id = "a2res"

    err1 = DNSAPIError("err1")

    # No records for no zones
    api = _TestZoneRecordSetAPI()
    assert api.add_record_sets({}) == {}
    api.assert_done()
    assert api.commands == []

    # No records for a zone
    api = _TestZoneRecordSetAPI()
    assert api.add_record_sets({1: []}) == {1: []}
    api.assert_done()
    assert api.commands == []

    # Two records
    api = _TestZoneRecordSetAPI()
    api.add_record_set_return_values = [a1res, a2res]
    assert api.add_record_sets({1: [a1, a2]}) == {
        1: [
            (a1res, True, None),
            (a2res, True, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("add_record_set", 1, a1),
        ("add_record_set", 1, a2),
    ]

    # Error with stopping early
    api = _TestZoneRecordSetAPI()
    api.add_record_set_return_values = [err1]
    assert api.add_record_sets({1: [a1, a2]}, stop_early_on_errors=True) == {
        1: [
            (a1, False, err1),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("add_record_set", 1, a1),
    ]

    # Error without stopping early
    api = _TestZoneRecordSetAPI()
    api.add_record_set_return_values = [err1, a2res]
    assert api.add_record_sets({1: [a1, a2]}, stop_early_on_errors=False) == {
        1: [
            (a1, False, err1),
            (a2res, True, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("add_record_set", 1, a1),
        ("add_record_set", 1, a2),
    ]


def test_update_record_sets():
    a1 = DNSRecordSet()
    a1.id = "a1"
    a2 = DNSRecordSet()
    a2.id = "a2"

    a1res = DNSRecordSet()
    a1res.id = "a1res"
    a2res = DNSRecordSet()
    a2res.id = "a2res"

    err1 = DNSAPIError("err1")

    # No records for no zones
    api = _TestZoneRecordSetAPI()
    assert api.update_record_sets({}) == {}
    api.assert_done()
    assert api.commands == []

    # No records for a zone
    api = _TestZoneRecordSetAPI()
    assert api.update_record_sets({1: []}) == {1: []}
    api.assert_done()
    assert api.commands == []

    # Two records
    api = _TestZoneRecordSetAPI()
    api.update_record_set_return_values = [a1res, a2res]
    assert api.update_record_sets({1: [(a1, True, False), (a2, False, True)]}) == {
        1: [
            (a1res, True, None),
            (a2res, True, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("update_record_set", 1, a1, True, False),
        ("update_record_set", 1, a2, False, True),
    ]

    # Error with stopping early
    api = _TestZoneRecordSetAPI()
    api.update_record_set_return_values = [err1]
    assert api.update_record_sets({1: [(a1, True, False), (a2, False, True)]}, stop_early_on_errors=True) == {
        1: [
            (a1, False, err1),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("update_record_set", 1, a1, True, False),
    ]

    # Error without stopping early
    api = _TestZoneRecordSetAPI()
    api.update_record_set_return_values = [err1, a2res]
    assert api.update_record_sets({1: [(a1, True, False), (a2, False, True)]}, stop_early_on_errors=False) == {
        1: [
            (a1, False, err1),
            (a2res, True, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("update_record_set", 1, a1, True, False),
        ("update_record_set", 1, a2, False, True),
    ]


def test_delete_record_sets():
    a1 = DNSRecordSet()
    a1.id = "a1"
    a2 = DNSRecordSet()
    a2.id = "a2"

    err1 = DNSAPIError("err1")

    # No records for no zones
    api = _TestZoneRecordSetAPI()
    assert api.delete_record_sets({}) == {}
    api.assert_done()
    assert api.commands == []

    # No records for a zone
    api = _TestZoneRecordSetAPI()
    assert api.delete_record_sets({1: []}) == {1: []}
    api.assert_done()
    assert api.commands == []

    # Two records
    api = _TestZoneRecordSetAPI()
    api.delete_record_set_return_values = [True, False]
    assert api.delete_record_sets({1: [a1, a2]}) == {
        1: [
            (a1, True, None),
            (a2, False, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("delete_record_set", 1, a1),
        ("delete_record_set", 1, a2),
    ]

    # Error with stopping early
    api = _TestZoneRecordSetAPI()
    api.delete_record_set_return_values = [err1]
    assert api.delete_record_sets({1: [a1, a2]}, stop_early_on_errors=True) == {
        1: [
            (a1, False, err1),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("delete_record_set", 1, a1),
    ]

    # Error without stopping early
    api = _TestZoneRecordSetAPI()
    api.delete_record_set_return_values = [err1, True]
    assert api.delete_record_sets({1: [a1, a2]}, stop_early_on_errors=False) == {
        1: [
            (a1, False, err1),
            (a2, True, None),
        ],
    }
    api.assert_done()
    assert api.commands == [
        ("delete_record_set", 1, a1),
        ("delete_record_set", 1, a2),
    ]
