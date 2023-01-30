"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from collections.abc import Set
from typing import Any, Iterable, Union

from referencing import Anchor, Registry, Resource, Specification
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


def _dollar_id_pre2019(contents: Schema) -> URI | None:
    if isinstance(contents, bool) or "$ref" in contents:
        return
    id = contents.get("$id")
    if id is not None and not id.startswith("#"):
        return id


def _legacy_id(contents: ObjectSchema) -> URI | None:
    return contents.get("id")


def _legacy_anchor_in_id(
    specification: Specification[ObjectSchema],
    contents: ObjectSchema,
) -> Iterable[Anchor[ObjectSchema]]:
    id = contents.get("$id", "")
    if not id.startswith("#"):
        return []
    return [
        Anchor(
            name=id[1:],
            resource=specification.create_resource(contents),
        ),
    ]


def _subresources_of(
    in_value: Set[str] = frozenset(),
    in_subvalues: Set[str] = frozenset(),
    in_subarray: Set[str] = frozenset(),
):
    """
    Create a callable returning JSON Schema specification-style subschemas.

    Relies on specifying the set of keywords containing subschemas in their
    values, in a subobject's values, or in a subarray.
    """

    def subresources_of(resource: ObjectSchema) -> Iterable[ObjectSchema]:
        for each in in_value:
            if each in resource:
                yield resource[each]
        for each in in_subarray:
            if each in resource:
                yield from resource[each]
        for each in in_subvalues:
            if each in resource:
                yield from resource[each].values()

    return subresources_of


DRAFT202012 = Specification(
    name="draft2020-12",
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
)
DRAFT201909 = Specification(
    name="draft2019-09",
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
)
DRAFT7 = Specification(
    name="draft-07",
    id_of=_dollar_id_pre2019,
    subresources_of=_subresources_of(
        in_value={"if", "then", "else"},
        in_subarray={"allOf", "anyOf", "oneOf"},
        in_subvalues={"definitions"},
    ),
    anchors_in=_legacy_anchor_in_id,
)
DRAFT6 = Specification(
    name="draft-06",
    id_of=_dollar_id,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
)
DRAFT4 = Specification(
    name="draft-04",
    id_of=_legacy_id,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
)
DRAFT3 = Specification(
    name="draft-03",
    id_of=_legacy_id,
    subresources_of=lambda contents: [],
    anchors_in=lambda specification, contents: [],
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
