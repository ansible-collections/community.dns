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
    import antsibull_nox.sessions
except ImportError:
    print("You need to install antsibull-nox in the same Python environment as nox.")
    sys.exit(1)


IN_CI = os.environ.get("CI") == "true"


antsibull_nox.add_lint_sessions(
    extra_code_files=["update-docs-fragments.py"],
    isort_config="tests/nox-config-isort.cfg",
    run_black_modules=False,  # modules still support Python 2
    black_config="tests/nox-config-black.toml",
    flake8_config="tests/nox-config-flake8.ini",
    pylint_rcfile="tests/nox-config-pylint.rc",
    pylint_modules_rcfile="tests/nox-config-pylint-py2.rc",
    run_yamllint=True,
    yamllint_config="tests/nox-config-yamllint.yml",
    mypy_config="tests/nox-config-mypy.ini",
    mypy_extra_deps=[
        "dnspython",
        "types-lxml",
        "types-mock",
        "types-PyYAML",
    ],
)

antsibull_nox.add_docs_check(
    validate_collection_refs="all",
)

antsibull_nox.add_license_check()

antsibull_nox.add_extra_checks(
    run_no_unwanted_files=True,
    no_unwanted_files_module_extensions=[".py"],
    no_unwanted_files_skip_paths=[
        "plugins/public_suffix_list.dat",
        "plugins/public_suffix_list.dat.license",
    ],
    no_unwanted_files_yaml_extensions=[".yml"],
    run_action_groups=True,
    action_groups_config=[
        antsibull_nox.ActionGroup(
            name="hetzner",
            pattern="^hetzner_.*$",
            exclusions=[],
            doc_fragment="community.dns.attributes.actiongroup_hetzner",
        ),
        antsibull_nox.ActionGroup(
            name="hosttech",
            pattern="^hosttech_.*$",
            exclusions=[],
            doc_fragment="community.dns.attributes.actiongroup_hosttech",
        ),
    ],
)


antsibull_nox.add_build_import_check(
    run_galaxy_importer=True,
)


@nox.session(name="update-docs-fragments", default=True)
def update_docs_fragments(session: nox.Session) -> None:
    """
    Update/check auto-generated parts of docs fragments.
    """
    antsibull_nox.sessions.install(session, "ansible-core")
    prepare = antsibull_nox.sessions.prepare_collections(
        session, install_in_site_packages=True
    )
    if not prepare:
        return
    data = ["python", "update-docs-fragments.py"]
    if IN_CI:
        data.append("--lint")
    session.run(*data)


antsibull_nox.add_all_ansible_test_sanity_test_sessions(include_devel=True)
antsibull_nox.add_all_ansible_test_unit_test_sessions(include_devel=True)
antsibull_nox.add_ansible_test_integration_sessions_default_container(
    core_python_versions={
        "2.14": ["2.7", "3.5", "3.9"],
        "2.15": ["3.7"],
        "2.16": ["2.7", "3.6", "3.11"],
        "2.17": ["3.7", "3.12"],
        "2.18": ["3.8", "3.13"],
    },
    include_devel=True,
)


antsibull_nox.add_matrix_generator()


# Allow to run the noxfile with `python noxfile.py`, `pipx run noxfile.py`, or similar.
# Requires nox >= 2025.02.09
if __name__ == "__main__":
    nox.main()
