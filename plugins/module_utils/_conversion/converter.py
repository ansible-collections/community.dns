# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

# Note that this module util is **PRIVATE** to the collection. It can have breaking changes at any time.
# Do not use this from other collections or standalone plugins/modules!

from __future__ import annotations

import typing as t

from ansible.module_utils.common.text.converters import to_text

from ansible_collections.community.dns.plugins.module_utils._conversion.base import (
    DNSConversionError,
)
from ansible_collections.community.dns.plugins.module_utils._conversion.txt import (
    decode_txt_value,
    encode_txt_value,
)
from ansible_collections.community.dns.plugins.module_utils._record import DNSRecord

if t.TYPE_CHECKING:
    from collections.abc import Sequence  # pragma: no cover

    from .._argspec import OptionProvider  # pragma: no cover
    from .._provider import ProviderInformation  # pragma: no cover
    from .._record import RecordIDT  # pragma: no cover
    from .._record_set import DNSRecordSet, RecordSetIDT  # pragma: no cover


class RecordConverter:
    def __init__(
        self, provider_information: ProviderInformation, option_provider: OptionProvider
    ) -> None:
        """
        Create a record converter.
        """
        self._provider_information = provider_information
        self._option_provider = option_provider

        # Valid values: 'decoded', 'encoded', 'encoded-no-char-encoding'
        self._txt_api_handling = self._provider_information.txt_record_handling()
        self._txt_api_character_encoding = (
            self._provider_information.txt_character_encoding()
        )
        self._txt_always_quote = self._provider_information.txt_always_quote()
        # Valid values: 'api', 'quoted', 'unquoted'
        self._txt_transformation = self._option_provider.get_option(
            "txt_transformation"
        )
        # Valid values: 'decimal', 'octal'
        self._txt_character_encoding = self._option_provider.get_option(
            "txt_character_encoding"
        )

    def emit_deprecations(self, deprecator: t.Callable[[str], None]) -> None:
        pass

    def _handle_txt_api(self, to_api: bool, record: DNSRecord[RecordIDT]) -> None:
        """
        Handle TXT records for sending to/from the API.
        """
        if self._txt_transformation == "api":
            # Do not touch record values
            return

        # We assume that records internally use decoded values
        if self._txt_api_handling in (
            "encoded",
            "encoded-no-char-encoding",
        ):
            if to_api:
                record.target = encode_txt_value(
                    record.target,
                    always_quote=self._txt_always_quote,
                    use_character_encoding=self._txt_api_handling == "encoded",
                    character_encoding=self._txt_api_character_encoding,
                )
            else:
                record.target = decode_txt_value(
                    record.target, character_encoding=self._txt_api_character_encoding
                )

    def _handle_txt_user(self, to_user: bool, record: DNSRecord[RecordIDT]) -> None:
        """
        Handle TXT records for sending to/from the user.
        """
        if self._txt_transformation == "api":
            # Do not touch record values
            return

        # We assume that records internally use decoded values
        if self._txt_transformation == "quoted":
            if to_user:
                record.target = encode_txt_value(
                    record.target, character_encoding=self._txt_character_encoding
                )
            else:
                record.target = decode_txt_value(
                    record.target, character_encoding=self._txt_character_encoding
                )

    def process_from_api(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) after receiving from API.
        Modifies the record in-place.
        """
        try:
            record.target = to_text(record.target)
            if record.type == "TXT":
                self._handle_txt_api(False, record)
            return record
        except DNSConversionError as e:
            raise DNSConversionError(
                f"While processing record from API: {e.error_message}"
            ) from e

    def process_to_api(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) for sending to API.
        Modifies the record in-place.
        """
        try:
            if record.type == "TXT":
                self._handle_txt_api(True, record)
            return record
        except DNSConversionError as e:  # pragma: no cover
            # This can never happen
            raise DNSConversionError(
                f"While processing record for the API: {e.error_message}"
            ) from e  # pragma: no cover

    def process_from_user(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) after receiving from the user.
        Modifies the record in-place.
        """
        try:
            record.target = to_text(record.target)
            if record.type == "TXT":
                self._handle_txt_user(False, record)
            return record
        except DNSConversionError as e:
            raise DNSConversionError(
                f"While processing record from the user: {e.error_message}"
            ) from e

    def process_to_user(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) for sending to the user.
        Modifies the record in-place.
        """
        try:
            if record.type == "TXT":
                self._handle_txt_user(True, record)
            return record
        except DNSConversionError as e:  # pragma: no cover
            # This can never happen
            raise DNSConversionError(
                f"While processing record for the user: {e.error_message}"
            ) from e  # pragma: no cover

    def clone_from_api(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) after receiving from API.
        Return a modified clone of the record; the original will not be modified.
        """
        record = record.clone()
        self.process_from_api(record)
        return record

    def clone_to_api(self, record: DNSRecord[RecordIDT]) -> DNSRecord[RecordIDT]:
        """
        Process a record object (DNSRecord) for sending to API.
        Return a modified clone of the record; the original will not be modified.
        """
        record = record.clone()
        self.process_to_api(record)
        return record

    def clone_multiple_from_api(
        self, records: Sequence[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record object (DNSRecord) after receiving from API.
        Return a list of modified clones of the records; the originals will not be modified.
        """
        return [self.clone_from_api(record) for record in records]

    def clone_multiple_to_api(
        self, records: Sequence[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record objects (DNSRecord) for sending to API.
        Return a list of modified clones of the records; the originals will not be modified.
        """
        return [self.clone_to_api(record) for record in records]

    def clone_set_to_api(
        self, record_set: DNSRecordSet[RecordSetIDT, RecordIDT]
    ) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        """
        Process a record set object (DNSRecordSet) for sending to API.
        Return a modified clone of the record set; the original will not be modified.
        """
        record_set = record_set.clone()
        record_set.records = [
            self.clone_to_api(record) for record in record_set.records
        ]
        return record_set

    def process_multiple_from_api(
        self, records: list[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record object (DNSRecord) after receiving from API.
        Modifies the records in-place.
        """
        for record in records:
            self.process_from_api(record)
        return records

    def process_multiple_to_api(
        self, records: list[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record objects (DNSRecord) for sending to API.
        Modifies the records in-place.
        """
        for record in records:
            self.process_to_api(record)
        return records

    def process_multiple_from_user(
        self, records: list[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record object (DNSRecord) after receiving from the user.
        Modifies the records in-place.
        """
        for record in records:
            self.process_from_user(record)
        return records

    def process_multiple_to_user(
        self, records: list[DNSRecord[RecordIDT]]
    ) -> list[DNSRecord[RecordIDT]]:
        """
        Process a list of record objects (DNSRecord) for sending to the user.
        Modifies the records in-place.
        """
        for record in records:
            self.process_to_user(record)
        return records

    def process_set_from_api(
        self, record_set: DNSRecordSet[RecordSetIDT, RecordIDT]
    ) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        """
        Process a record set object (DNSRecordSet) after receiving from API.
        Modifies the records in-place.
        """
        for record in record_set.records:
            self.process_from_api(record)
        return record_set

    def process_set_to_api(
        self, record_set: DNSRecordSet[RecordSetIDT, RecordIDT]
    ) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        """
        Process a record set object (DNSRecordSet) for sending to API.
        Modifies the records in-place.
        """
        for record in record_set.records:
            self.process_to_api(record)
        return record_set

    def process_set_from_user(
        self, record_set: DNSRecordSet[RecordSetIDT, RecordIDT]
    ) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        """
        Process a record set object (DNSRecordSet) after receiving from the user.
        Modifies the records in-place.
        """
        for record in record_set.records:
            self.process_from_user(record)
        return record_set

    def process_set_to_user(
        self, record_set: DNSRecordSet[RecordSetIDT, RecordIDT]
    ) -> DNSRecordSet[RecordSetIDT, RecordIDT]:
        """
        Process a record set objects (DNSRecordSet) for sending to the user.
        Modifies the records in-place.
        """
        for record in record_set.records:
            self.process_to_user(record)
        return record_set

    def process_value_from_user(self, record_type: str, value: str) -> str:
        """
        Process a record value (string) after receiving from the user.
        """
        record: DNSRecord[None] = DNSRecord(
            record_id=None, record_type=record_type, target=value
        )
        self.process_from_user(record)
        return record.target

    def process_values_from_user(
        self, record_type: str, values: Sequence[str]
    ) -> list[str]:
        """
        Process a list of record values (strings) after receiving from the user.
        """
        return [self.process_value_from_user(record_type, value) for value in values]

    def process_value_to_user(self, record_type: str, value: str) -> str:
        """
        Process a record value (string) for sending to the user.
        """
        record: DNSRecord[None] = DNSRecord(
            record_id=None, record_type=record_type, target=value
        )
        self.process_to_user(record)
        return record.target

    def process_values_to_user(
        self, record_type: str, values: Sequence[str]
    ) -> list[str]:
        """
        Process a list of record values (strings) for sending to the user.
        """
        return [self.process_value_to_user(record_type, value) for value in values]
