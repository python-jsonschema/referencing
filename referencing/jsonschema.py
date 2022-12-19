"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from referencing._attrs import frozen
from referencing._core import Anchor
from referencing.typing import Schema


class Draft202012:

    _SUBRESOURCE = {"items", "not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False:
            return
        return resource.get("$id")

    def anchors_in(self, resource):
        anchor = resource.get("$anchor")
        if anchor is not None:
            yield Anchor(name=anchor, resource=resource)

        dynamic_anchor = resource.get("$dynamicAnchor")
        if dynamic_anchor is not None:
            yield DynamicAnchor(name=dynamic_anchor, resource=resource)

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

    name: str
    resource: Schema

    def resolve(self, resolver, uri):
        last = self.resource
        for resource, anchors in resolver.dynamic_scope():
            anchor = anchors.get(self.name)
            if isinstance(anchor, DynamicAnchor):
                last = anchor.resource
            elif "$ref" not in resource:
                break
        id = resolver._registry._specification.id_of(last) or ""  # FIXME
        return last, id


class Draft201909:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False:
            return
        return resource.get("$id")

    def anchors_in(self, resource):
        anchor = resource.get("$anchor")
        if anchor is not None:
            yield Anchor(name=anchor, resource=resource)

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


class Draft7:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"definitions", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False or "$ref" in resource:
            return None
        id = resource.get("$id")
        if id is not None and not id.startswith("#"):
            return id

    def anchors_in(self, resource):
        anchor = resource.get("$id", "")
        if anchor.startswith("#"):
            yield Anchor(name=anchor[1:], resource=resource)

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


class Draft6:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"definitions", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False or "$ref" in resource:
            return None
        id = resource.get("$id")
        if id is not None and not id.startswith("#"):
            return id

    def anchors_in(self, resource):
        anchor = resource.get("$id", "")
        if anchor.startswith("#"):
            yield Anchor(name=anchor[1:], resource=resource)

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


class Draft4:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"definitions", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False or "$ref" in resource:
            return None
        id = resource.get("id")
        if id is None or id.startswith("#"):
            return
        return id

    def anchors_in(self, resource):
        anchor = self.id_of(resource) or ""
        if anchor.startswith("#"):
            yield Anchor(name=anchor[1:], resource=resource)

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


class Draft3:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"definitions", "properties"}

    def id_of(self, resource):
        if resource is True or resource is False or "$ref" in resource:
            return None
        id = resource.get("id")
        if id is not None and not id.startswith("#"):
            return id

    def anchors_in(self, resource):
        anchor = resource.get("id", "")
        if anchor.startswith("#"):
            yield Anchor(name=anchor[1:], resource=resource)

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
