from pathlib import Path
import json
import os

import pytest

from referencing import Registry, Resource


class SuiteNotFound(Exception):
    def __str__(self):
        return (
            "Cannot find the referencing suite. "
            "Set the REFERENCING_SUITE environment variable to the path to "
            "the suite, or run the test suite from alongside a full checkout "
            "of the git repository."
        )


if "REFERENCING_SUITE" in os.environ:
    REFERENCING_SUITE = Path(os.environ["REFERENCING_SUITE"]) / "tests"
else:
    REFERENCING_SUITE = Path(__file__).parent.parent.parent / "suite/tests"
if not REFERENCING_SUITE.is_dir():
    raise SuiteNotFound()


@pytest.mark.parametrize("test_path", REFERENCING_SUITE.rglob("*.json"))
def test_referencing_suite(test_path):
    loaded = json.loads(test_path.read_text())
    registry = loaded["registry"]
    registry = Registry().with_resources(
        (uri, Resource.opaque(contents=contents))
        for uri, contents in loaded["registry"].items()
    )
    for test in loaded["tests"]:
        resolver = registry.resolver(base_uri=test.get("base_uri", ""))
        assert resolver.lookup(test["ref"]).contents == test["target"]
