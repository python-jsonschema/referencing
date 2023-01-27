from pathlib import Path
import json
import os

import pytest

from referencing import Registry
import referencing.jsonschema


class SuiteNotFound(Exception):
    def __str__(self):
        return (
            "Cannot find the referencing suite. "
            "Set the REFERENCING_SUITE environment variable to the path to "
            "the suite, or run the test suite from alongside a full checkout "
            "of the git repository."
        )


if "REFERENCING_SUITE" in os.environ:
    SUITE = Path(os.environ["REFERENCING_SUITE"]) / "tests"
else:
    SUITE = Path(__file__).parent.parent.parent / "suite/tests"
if not SUITE.is_dir():
    raise SuiteNotFound()
DIALECT_IDS = json.loads(SUITE.joinpath("specifications.json").read_text())


@pytest.mark.parametrize("test_path", SUITE.glob("*/**/*.json"))
def test_referencing_suite(test_path):
    dialect_id = DIALECT_IDS[test_path.relative_to(SUITE).parts[0]]
    specification = referencing.jsonschema.specification_with(dialect_id)
    loaded = json.loads(test_path.read_text())
    registry = loaded["registry"]
    registry = Registry().with_resources(
        (uri, specification.create_resource(contents))
        for uri, contents in loaded["registry"].items()
    )
    for test in loaded["tests"]:
        resolver = registry.resolver(base_uri=test.get("base_uri", ""))
        assert resolver.lookup(test["ref"]).contents == test["target"]