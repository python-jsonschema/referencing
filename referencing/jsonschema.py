"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from urllib.parse import urljoin

from referencing._attrs import frozen
from referencing._core import (
    Anchor,
    IdentifiedResource,
    Resolver,
    Specification,
)
from referencing.typing import ObjectSchema, Schema


def _dollar_id(resource: Schema):
    if resource is True or resource is False:
        return
    return resource.get("$id")


def _dollar_id_pre2019(resource: Schema):
    if resource is True or resource is False or "$ref" in resource:
        return None
    id = resource.get("$id")
    if id is not None and not id.startswith("#"):
        return id


def _id_no_ref(resource):
    if "$ref" not in resource:
        id = resource.get("id")
        if id is not None and not id.startswith("#"):
            return id


def _anchor_or_dynamic_anchor(
    resource: ObjectSchema,
    specification: Specification,
):
    anchor = resource.get("$anchor")
    if anchor is not None:
        yield Anchor(
            name=anchor,
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        )

    dynamic_anchor = resource.get("$dynamicAnchor")
    if dynamic_anchor is not None:
        yield DynamicAnchor(
            name=dynamic_anchor,
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        )


def _subresources_of(subresource, in_items, in_values):
    def subresources_of(resource):
        for each in subresource:
            if each in resource:
                yield resource[each]
        for each in in_items:
            if each in resource:
                yield from resource[each]
        for each in in_values:
            if each in resource:
                yield from resource[each].values()

    return subresources_of


def _subresources_of_pre2020(subresource, in_items, in_values):
    def subresources_of(resource):
        for each in subresource:
            if each in resource:
                yield resource[each]
        for each in in_items:
            if each in resource:
                yield from resource[each]
        for each in in_values:
            if each in resource:
                yield from resource[each].values()

        items = resource.get("items")
        if items is None:
            return
        elif isinstance(items, list):
            yield from items
        else:
            yield items

    return subresources_of


DRAFT202012 = Specification(
    id_of=_dollar_id,
    anchors_in=_anchor_or_dynamic_anchor,
    subresources_of=_subresources_of(
        subresource={"items", "not"},
        in_items={"allOf"},
        in_values={"$defs", "properties"},
    ),
)


DRAFT201909 = Specification(
    id_of=_dollar_id,
    anchors_in=lambda resource, specification: [
        Anchor(
            name=resource["$anchor"],
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        ),
    ]
    if "$anchor" in resource
    else [],
    subresources_of=_subresources_of_pre2020(
        subresource={"not"},
        in_items={"allOf"},
        in_values={"$defs", "properties"},
    ),
)


DRAFT7 = Specification(
    id_of=_dollar_id_pre2019,
    anchors_in=lambda resource, specification: [
        Anchor(
            name=resource["$id"][1:],
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        ),
    ]
    if resource.get("$id", "").startswith("#")
    else [],
    subresources_of=_subresources_of_pre2020(
        subresource={"not"},
        in_items={"allOf"},
        in_values={"definitions", "properties"},
    ),
)


DRAFT6 = Specification(
    id_of=_dollar_id_pre2019,
    anchors_in=lambda resource, specification: [
        Anchor(
            name=resource["$id"][1:],
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        ),
    ]
    if resource.get("$id", "").startswith("#")
    else [],
    subresources_of=_subresources_of_pre2020(
        subresource={"not"},
        in_items={"allOf"},
        in_values={"definitions", "properties"},
    ),
)


DRAFT4 = Specification(
    id_of=_id_no_ref,
    anchors_in=lambda resource, specification: [
        Anchor(
            name=resource["id"][1:],
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        ),
    ]
    if resource.get("id", "").startswith("#")
    else [],
    subresources_of=_subresources_of_pre2020(
        subresource={"not"},
        in_items={"allOf"},
        in_values={"definitions", "properties"},
    ),
)


DRAFT3 = Specification(
    id_of=_id_no_ref,
    anchors_in=lambda resource, specification: [
        Anchor(
            name=resource["id"][1:],
            resource=IdentifiedResource(
                resource=resource,
                specification=specification,
            ),
        ),
    ]
    if resource.get("id", "").startswith("#")
    else [],
    subresources_of=_subresources_of_pre2020(
        subresource={"not"},
        in_items={"allOf"},
        in_values={"definitions", "properties"},
    ),
)


@frozen
class DynamicAnchor:
    """
    Dynamic anchors, introduced in draft 2020.
    """

    name: str
    resource: IdentifiedResource

    def resolve(self, resolver, uri):
        last = self.resource
        for _, resource, anchors in resolver.dynamic_scope():
            anchor = anchors.get(self.name)
            if isinstance(anchor, DynamicAnchor):
                last = anchor.resource
            elif "$ref" not in resource.resource:
                break
        return last, last.id() or ""


def lookup_recursive_ref(
    resolver: Resolver,
    recursiveRef: str,
) -> tuple[Schema, Resolver]:
    """
    Recursive references (via recursive anchors), present only in draft 2019.
    """
    subschema, resolver = resolver.lookup(recursiveRef)
    if subschema.get("$recursiveAnchor"):  # type: ignore # FIXME: missing test
        for uri, _, _ in resolver.dynamic_scope():
            ref = urljoin(uri, recursiveRef)
            next_subschema, next_resolver = resolver.lookup(ref)
            if not next_subschema.get("$recursiveAnchor"):  # type: ignore
                break
            subschema, resolver = next_subschema, next_resolver
    return subschema, resolver


BY_ID = {
    "https://json-schema.org/draft/2020-12/schema": DRAFT202012,
    "https://json-schema.org/draft/2019-09/schema": DRAFT201909,
    "http://json-schema.org/draft-07/schema#": DRAFT7,
    "http://json-schema.org/draft-06/schema#": DRAFT6,
    "http://json-schema.org/draft-04/schema#": DRAFT4,
    "http://json-schema.org/draft-03/schema#": DRAFT3,
}
