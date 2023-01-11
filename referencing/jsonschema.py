"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from typing import Any, Union

from referencing import Registry, Resource, Specification
from referencing._attrs import frozen
from referencing.typing import URI, Mapping

#: A JSON Schema which is a JSON object
ObjectSchema = Mapping[str, Any]

#: A JSON Schema of any kind
Schema = Union[bool, ObjectSchema]


@frozen
class UnknownDialect(Exception):
    """
    A dialect identifier was found for a dialect unknown by this library.

    If it's a custom ("unofficial") dialect, be sure you've registered it.
    """

    uri: URI


def _dollar_id(contents: Schema) -> URI | None:
    if isinstance(contents, bool):
        return
    return contents.get("$id")


def _legacy_id(contents: ObjectSchema) -> URI | None:
    return contents.get("id")


DRAFT202012 = Specification(id_of=_dollar_id)
DRAFT201909 = Specification(id_of=_dollar_id)
DRAFT7 = Specification(id_of=_dollar_id)
DRAFT6 = Specification(id_of=_dollar_id)
DRAFT4 = Specification(id_of=_legacy_id)
DRAFT3 = Specification(id_of=_legacy_id)


_SPECIFICATIONS: Registry[Specification[Schema]] = Registry().with_resources(  # type: ignore[reportUnknownMemberType]  # noqa: E501
    (dialect_id, Resource(contents=specification, specification=specification))  # type: ignore[reportUnknownArgumentType]  # noqa: E501
    for dialect_id, specification in [
        ("https://json-schema.org/draft/2020-12/schema", DRAFT202012),
        ("https://json-schema.org/draft/2019-09/schema", DRAFT201909),
        ("http://json-schema.org/draft-07/schema#", DRAFT7),
        ("http://json-schema.org/draft-06/schema#", DRAFT6),
        ("http://json-schema.org/draft-04/schema#", DRAFT4),
        ("http://json-schema.org/draft-03/schema#", DRAFT3),
    ]
)


def specification_with(
    dialect_id: URI,
    default: Specification[Any] = None,  # type: ignore[reportGeneralTypeIssues]  # noqa: E501
) -> Specification[Any]:
    """
    Retrieve the `Specification` with the given dialect identifier.

    Raises:

        `UnknownDialect`

            if the given ``dialect_id`` isn't known
    """
    resource = _SPECIFICATIONS.get(dialect_id)
    if resource is not None:
        return resource.contents
    if default is None:
        raise UnknownDialect(dialect_id)
    return default
