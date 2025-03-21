# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Felix Fontein <felix@fontein.de>

# /// script
# dependencies = ["nox>=2025.02.09", "antsibull-nox"]
# ///

import os
import sys

import nox


try:
    import antsibull_nox
except ImportError:
    print("You need to install antsibull-nox in the same Python environment as nox.")
    sys.exit(1)


# Always install latest pip version
os.environ["VIRTUALENV_DOWNLOAD"] = "1"


antsibull_nox.add_lint_sessions(
    isort_config="tests/nox-config-isort.cfg",
    run_black_modules=False,  # modules still support Python 2
    black_config="tests/nox-config-black.toml",
    flake8_config="tests/nox-config-flake8.ini",
    pylint_rcfile="tests/nox-config-pylint.rc",
    pylint_modules_rcfile="tests/nox-config-pylint-py2.rc",
    mypy_config="tests/nox-config-mypy.ini",
    mypy_extra_deps=[
        "dnspython",
        "types-lxml",
        "types-mock",
    ],
)


# Allow to run the noxfile with `python noxfile.py`, `pipx run noxfile.py`, or similar.
# Requires nox >= 2025.02.09
if __name__ == "__main__":
    nox.main()
