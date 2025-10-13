from pathlib import Path
from tempfile import TemporaryDirectory
import os

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
DOCS = ROOT / "docs"
REFERENCING = ROOT / "referencing"

REQUIREMENTS = dict(
    docs=DOCS / "requirements.txt",
    tests=ROOT / "test-requirements.txt",
)
REQUIREMENTS_IN = [  # this is actually ordered, as files depend on each other
    (path.parent / f"{path.stem}.in", path) for path in REQUIREMENTS.values()
]

SUPPORTED = [
    "3.9",
    "3.10",
    "pypy3.11",
    "3.11",
    "3.12",
    "3.13",
    "3.14t",
    "3.14",
]
LATEST = SUPPORTED[-1]

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = []


def session(default=True, python=LATEST, **kwargs):  # noqa: D103
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(python=python, **kwargs)(fn)

    return _session


@session(python=SUPPORTED)
def tests(session):
    """
    Run the test suite with a corresponding Python version.
    """
    session.install("-r", REQUIREMENTS["tests"])

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            github = Path(os.environ["GITHUB_STEP_SUMMARY"])
        else:
            github = None

        session.install("coverage[toml]")
        session.run("coverage", "run", "-m", "pytest", REFERENCING)
        if github is None:
            session.run("coverage", "report")
        else:
            with github.open("a") as summary:
                summary.write("### Coverage\n\n")
                summary.flush()  # without a flush, output seems out of order.
                session.run(
                    "coverage",
                    "report",
                    "--format=markdown",
                    stdout=summary,
                )
    else:
        session.run("pytest", *session.posargs, REFERENCING)


@session(tags=["build"])
def build(session):
    """
    Build a distribution suitable for PyPI and check its validity.
    """
    session.install("build[uv]", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run(
            "pyproject-build",
            "--installer=uv",
            ROOT,
            "--outdir",
            tmpdir,
        )
        session.run("twine", "check", "--strict", tmpdir + "/*")


@session(tags=["style"])
def style(session):
    """
    Check Python code style.
    """
    session.install("ruff")
    session.run("ruff", "check", ROOT, __file__)


@session()
def typing(session):
    """
    Check static typing.
    """
    session.install("pyright", ROOT)
    session.run("pyright", *session.posargs, REFERENCING)


@session()
def mypy(session):
    """
    Check that mypy runs with no blocking errors.
    """
    session.install("mypy", ROOT)
    session.run("mypy", REFERENCING)


@session(tags=["docs"])
@nox.parametrize(
    "builder",
    [
        nox.param(name, id=name)
        for name in [
            "dirhtml",
            "doctest",
            "linkcheck",
            "man",
            "spelling",
        ]
    ],
)
def docs(session, builder):
    """
    Build the documentation using a specific Sphinx builder.
    """
    session.install("-r", REQUIREMENTS["docs"])
    with TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        argv = ["-n", "-T", "-W"]
        if builder != "spelling":
            argv += ["-q"]
        posargs = session.posargs or [tmpdir / builder]
        session.run(
            "python",
            "-m",
            "sphinx",
            "-b",
            builder,
            DOCS,
            *argv,
            *posargs,
        )


@session(tags=["docs", "style"], name="docs(style)")
def docs_style(session):
    """
    Check the documentation style.
    """
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", "--config", PYPROJECT, DOCS)


@session(default=False)
def requirements(session):
    """
    Update the project's pinned requirements.

    You should commit the result afterwards.
    """
    if session.venv_backend == "uv":
        cmd = ["uv", "pip", "compile"]
    else:
        session.install("pip-tools")
        cmd = ["pip-compile", "--resolver", "backtracking", "--strip-extras"]

    for each, out in REQUIREMENTS_IN:
        # otherwise output files end up with silly absolute path comments...
        relative = each.relative_to(ROOT)
        session.run(*cmd, "--upgrade", "--output-file", out, relative)
