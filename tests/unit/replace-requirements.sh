#!/usr/bin/env bash
# Copyright (c) Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

DIRECTORY="$(dirname "$0")"

if [ -e "${DIRECTORY}/$1" ]; then
    cp "${DIRECTORY}/$1" "${DIRECTORY}/requirements.txt"
fi
