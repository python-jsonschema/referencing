from pathlib import Path
from tempfile import TemporaryDirectory
import os

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
DOCS = ROOT / "docs"
REFERENCING = ROOT / "referencing"


nox.options.sessions = []


def session(default=True, **kwargs):  # noqa: D103
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(**kwargs)(fn)

    return _session


@session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "pypy3"])
def tests(session):
    """
    Run the test suite with a corresponding Python version.
    """
    session.install("-r", ROOT / "test-requirements.txt")

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            github = os.environ["GITHUB_STEP_SUMMARY"]
        else:
            github = None

        session.install("coverage[toml]")
        session.run("coverage", "run", "-m", "pytest", REFERENCING)
        if github is None:
            session.run("coverage", "report")
        else:
            with open(github, "a") as summary:
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


@session()
def audit(session):
    """
    Audit dependencies for vulnerabilities.
    """
    session.install("pip-audit", ROOT)
    session.run("python", "-m", "pip_audit")


@session(tags=["build"])
def build(session):
    """
    Build a distribution suitable for PyPI and check its validity.
    """
    session.install("build", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")


@session(tags=["style"])
def style(session):
    """
    Check Python code style.
    """
    session.install("ruff")
    session.run("ruff", "check", ROOT)


@session()
def typing(session):
    """
    Check static typing.
    """
    session.install("pyright==1.1.307", ROOT)
    session.run("pyright", REFERENCING)


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
    session.install("-r", DOCS / "requirements.txt")
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
    Update the project's pinned requirements. Commit the result.
    """
    session.install("pip-tools")
    for each in [DOCS / "requirements.in", ROOT / "test-requirements.in"]:
        session.run(
            "pip-compile",
            "--resolver",
            "backtracking",
            "--strip-extras",
            "-U",
            each.relative_to(ROOT),
        )
