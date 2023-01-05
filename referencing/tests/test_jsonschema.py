import pytest

from referencing import Resource
import referencing.jsonschema


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "https://json-schema.org/draft/2020-12/schema",
            referencing.jsonschema.DRAFT202012,
        ),
        (
            "https://json-schema.org/draft/2019-09/schema",
            referencing.jsonschema.DRAFT201909,
        ),
        (
            "http://json-schema.org/draft-07/schema#",
            referencing.jsonschema.DRAFT7,
        ),
        (
            "http://json-schema.org/draft-06/schema#",
            referencing.jsonschema.DRAFT6,
        ),
        (
            "http://json-schema.org/draft-04/schema#",
            referencing.jsonschema.DRAFT4,
        ),
        (
            "http://json-schema.org/draft-03/schema#",
            referencing.jsonschema.DRAFT3,
        ),
    ],
)
def test_schemas_with_explicit_schema_keywords_are_detected(uri, expected):
    """
    The $schema keyword in JSON Schema is a dialect identifier.
    """
    contents = {"$schema": uri}
    resource = Resource.from_contents(contents)
    assert resource == Resource(contents=contents, specification=expected)
