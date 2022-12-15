"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from referencing._attrs import frozen
from referencing.typing import Schema


class Draft202012:

    _SUBRESOURCE = {"items", "not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def subresources_of(self, resource):
        for each in self._SUBRESOURCE:
            if each in resource:
                yield resource[each]
        for each in self._SUBRESOURCE_ITEMS:
            if each in resource:
                yield from resource[each]
        for each in self._SUBRESOURCE_VALUES:
            if each in resource:
                yield from resource[each].values()


@frozen
class DynamicAnchor:

    uri: str
    name: str
    resource: Schema

    def resolve(self, dynamic_scope, uri):
        last = self.resource
        for resource, anchors in dynamic_scope:
            anchor = anchors.get(self.name)
            if isinstance(anchor, DynamicAnchor):
                last = anchor.resource
            elif "$ref" not in resource:
                break
        return last, id_of(last) or ""  # FIXME: consider when this can be None


class Draft201909:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def subresources_of(self, resource):
        for each in self._SUBRESOURCE:
            if each in resource:
                yield resource[each]
        for each in self._SUBRESOURCE_ITEMS:
            if each in resource:
                yield from resource[each]
        for each in self._SUBRESOURCE_VALUES:
            if each in resource:
                yield from resource[each].values()

        items = resource.get("items")
        if items is None:
            return
        elif isinstance(items, list):
            yield from items
        else:
            yield items


def id_of(resource) -> str | None:
    if resource is True or resource is False:
        return None
    return resource.get("$id")
