# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 Felix Fontein <felix@fontein.de>

import contextlib
import os

import nox


IN_CI = "GITHUB_ACTIONS" in os.environ
ALLOW_EDITABLE = os.environ.get("ALLOW_EDITABLE", str(not IN_CI)).lower() in (
    "1",
    "true",
)
CODE_FILES = [
    "plugins",
    "tests/unit",
]

COLLECTION_NAME = "community.dns"

PYTHON_2_COMPATIBILITY = [
    "plugins/modules/",
    "plugins/module_utils/",
    "tests/unit/plugins/modules/",
    "tests/unit/plugins/module_utils/",
]

# Always install latest pip version
os.environ["VIRTUALENV_DOWNLOAD"] = "1"

# Default session is 'lint'
nox.options.sessions = ("lint",)


def install(session: nox.Session, *args, editable=False, **kwargs):
    # nox --no-venv
    if isinstance(session.virtualenv, nox.virtualenv.PassthroughEnv):
        session.warn(f"No venv. Skipping installation of {args}")
        return
    # Don't install in editable mode in CI or if it's explicitly disabled.
    # This ensures that the wheel contains all of the correct files.
    if editable and ALLOW_EDITABLE:
        args = ("-e", *args)
    session.install(*args, "-U", **kwargs)


@contextlib.contextmanager
def ansible_collection_root():
    cwd = os.getcwd()
    root = os.path.normpath(os.path.join(cwd, "..", "..", ".."))
    try:
        os.chdir(root)
        yield root, os.path.relpath(cwd, root)
    finally:
        os.chdir(cwd)


def prefix_paths(paths: list[str], /, prefix: str) -> list[str]:
    return [os.path.join(prefix, path) for path in paths]


def match_path(path: str, is_file: bool, paths: list[str]) -> bool:
    for check in paths:
        if check == path:
            return True
        if not is_file:
            if not check.endswith("/"):
                check += "/"
            if path.startswith(check):
                return True
    return False


def restrict_paths(paths: list[str], restrict: list[str]) -> list[str]:
    result = []
    for path in paths:
        is_file = os.path.isfile(path)
        if not is_file and not path.endswith("/"):
            path += "/"
        if not match_path(path, is_file, restrict):
            if not is_file:
                for check in restrict:
                    if check.startswith(path):
                        result.append(check)
            continue
        result.append(path)
    return result


def remove_paths(
    paths: list[str], remove: list[str], extensions: list[str] | None
) -> list[str]:
    result = []
    for path in paths:
        is_file = os.path.isfile(path)
        if not is_file and not path.endswith("/"):
            path += "/"
        if match_path(path, is_file, remove):
            continue
        if not is_file and any(check.startswith(path) for check in remove):
            for root, dirs, files in os.walk(path, topdown=True):
                if not root.endswith("/"):
                    root += "/"
                if match_path(root, False, remove):
                    continue
                if all(not check.startswith(root) for check in remove):
                    dirs[:] = []
                    result.append(root)
                    continue
                for file in files:
                    if extensions and os.path.splitext(file)[1] not in extensions:
                        continue
                    filepath = os.path.normpath(os.path.join(root, file))
                    if not match_path(filepath, True, remove):
                        result.append(filepath)
                for dir in list(dirs):
                    dirpath = os.path.normpath(os.path.join(root, dir))
                    if match_path(dirpath, False, remove):
                        dirs.remove(dir)
                        continue
            continue
        result.append(path)
    return result


def filter_paths(
    paths: list[str],
    /,
    remove: list[str] | None = None,
    restrict: list[str] | None = None,
    extensions: list[str] | None = None
) -> list[str]:
    if restrict:
        paths = restrict_paths(paths, restrict)
    if remove:
        paths = remove_paths(paths, remove, extensions)
    return paths


@nox.session
def lint(session: nox.Session):
    session.notify("formatters")
    session.notify("codeqa")
    session.notify("typing")


@nox.session
def formatters(session: nox.Session):
    install(session, "-r", "tests/nox-requirements-formatters.txt")
    posargs = list(session.posargs)
    if IN_CI:
        posargs.append("--check")
    session.run(
        "isort",
        *posargs,
        "--settings-file",
        "tests/nox-config-isort.cfg",
        *CODE_FILES,
        "noxfile.py",
    )
    # The last version of black that supports Python 2.7, 21.12b0, does not run on Python 3.13 -.-
    # Hence we have to restrict to Python 3 files for black
    py3_paths = filter_paths(
        CODE_FILES + ["noxfile.py"], remove=PYTHON_2_COMPATIBILITY, extensions=[".py"]
    )
    if py3_paths:
        session.run(
            "black", "--config", "tests/nox-config-black.toml", *posargs, *py3_paths
        )


@nox.session
def codeqa(session: nox.Session):
    install(session, "-r", "tests/nox-requirements-codeqa.txt")
    session.run(
        "flake8",
        "--config",
        "tests/nox-config-flake8.ini",
        *CODE_FILES,
        "noxfile.py",
        *session.posargs,
    )
    py2_paths = filter_paths(
        CODE_FILES, restrict=PYTHON_2_COMPATIBILITY, extensions=[".py"]
    )
    py3_paths = filter_paths(
        CODE_FILES, remove=PYTHON_2_COMPATIBILITY, extensions=[".py"]
    )
    with ansible_collection_root() as (root, prefix):
        if py2_paths:
            session.run(
                "pylint",
                "--rcfile",
                os.path.join(root, prefix, "tests/nox-config-pylint-py2.rc"),
                "--source-roots",
                root,
                *prefix_paths(py2_paths, prefix=prefix),
            )
        if py3_paths:
            session.run(
                "pylint",
                "--rcfile",
                os.path.join(root, prefix, "tests/nox-config-pylint.rc"),
                "--source-roots",
                root,
                *prefix_paths(py3_paths, prefix=prefix),
            )


@nox.session
def typing(session: nox.Session):
    install(session, "-r", "tests/nox-requirements-typing.txt")
    with ansible_collection_root() as (root, prefix):
        session.run(
            "mypy",
            "--config-file",
            os.path.join(root, prefix, "tests/nox-config-mypy.ini"),
            "--explicit-package-bases",
            *prefix_paths(CODE_FILES, prefix=prefix),
            env={"MYPYPATH": root},
        )
