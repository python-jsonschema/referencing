"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from referencing.typing import ObjectSchema


class Draft202012:

    _SUBRESOURCE = {"items", "not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def subresources_of(self, resource: ObjectSchema):
        for each in self._SUBRESOURCE:
            if each in resource:
                yield resource[each]
        for each in self._SUBRESOURCE_ITEMS:
            if each in resource:
                yield from resource[each]
        for each in self._SUBRESOURCE_VALUES:
            if each in resource:
                yield from resource[each].values()


class Draft201909:

    _SUBRESOURCE = {"not"}
    _SUBRESOURCE_ITEMS = {"allOf"}
    _SUBRESOURCE_VALUES = {"$defs", "properties"}

    def subresources_of(self, resource: ObjectSchema):
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
