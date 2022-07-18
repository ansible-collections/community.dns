#!/usr/bin/env python
# Copyright (c) 2021 Felix Fontein
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run update-docs-fragments.py --lint."""

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys
import subprocess


def main():
    """Main entry point."""
    p = subprocess.run([sys.executable, 'update-docs-fragments.py', '--lint'], check=False)
    if p.returncode not in (0, 5):
        print('{0}:0:0: unexpected return code {1}'.format(sys.argv[0], p.returncode))


if __name__ == '__main__':
    main()
