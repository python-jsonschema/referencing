"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from collections.abc import Set
from typing import Any, Iterable, Union

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


def _subresources_of(values: Set[str] = frozenset()):
    """
    Create a callable returning JSON Schema specification-style subschemas.

    Relies on specifying the set of keywords containing subschemas in their
    values, in a subobject's values, or in a subarray.
    """

    def subresources_of(resource: ObjectSchema) -> Iterable[ObjectSchema]:
        for each in values:
            if each in resource:
                yield resource[each]

    return subresources_of


DRAFT202012 = Specification(
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
)
DRAFT201909 = Specification(
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
)
DRAFT7 = Specification(
    id_of=_dollar_id,
    subresources_of=_subresources_of(values={"if", "then", "else"}),
)
DRAFT6 = Specification(
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
)
DRAFT4 = Specification(
    id_of=_legacy_id,
    subresources_of=lambda contents: [],
)
DRAFT3 = Specification(
    id_of=_legacy_id,
    subresources_of=lambda contents: [],
)


_SPECIFICATIONS: Registry[Specification[Schema]] = Registry(
    {  # type: ignore[reportGeneralTypeIssues]  # :/ internal vs external types
        dialect_id: Resource.opaque(specification)
        for dialect_id, specification in [
            ("https://json-schema.org/draft/2020-12/schema", DRAFT202012),
            ("https://json-schema.org/draft/2019-09/schema", DRAFT201909),
            ("http://json-schema.org/draft-07/schema#", DRAFT7),
            ("http://json-schema.org/draft-06/schema#", DRAFT6),
            ("http://json-schema.org/draft-04/schema#", DRAFT4),
            ("http://json-schema.org/draft-03/schema#", DRAFT3),
        ]
    },
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
