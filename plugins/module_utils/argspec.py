# -*- coding: utf-8 -*-
#
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


class ArgumentSpec(object):
    def __init__(self, argument_spec=None, required_together=None, required_if=None, mutually_exclusive=None):
        self.argument_spec = {}
        self.required_together = []
        self.required_if = []
        self.mutually_exclusive = []
        if argument_spec:
            self.argument_spec.update(argument_spec)
        if required_together:
            self.required_together.extend(required_together)
        if required_if:
            self.required_if.extend(required_if)
        if mutually_exclusive:
            self.mutually_exclusive.extend(mutually_exclusive)

    def merge(self, other):
        self.argument_spec.update(other.argument_spec)
        self.required_together.extend(other.required_together)
        self.required_if.extend(other.required_if)
        self.mutually_exclusive.extend(other.mutually_exclusive)

    def to_kwargs(self):
        return {
            'argument_spec': self.argument_spec,
            'required_together': self.required_together,
            'required_if': self.required_if,
            'mutually_exclusive': self.mutually_exclusive,
        }
