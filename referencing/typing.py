from typing import Any, Iterable, Protocol, Union

try:
    from collections.abc import Mapping

    Mapping[str, str]
except TypeError:
    from typing import Mapping

from referencing._core import Anchor, DynamicAnchor

ObjectSchema = Mapping[str, Any]
Schema = Union[bool, ObjectSchema]
AnchorType = Union[Anchor, DynamicAnchor]


class Specification(Protocol):
    def subresources_of(self, resource: ObjectSchema) -> Iterable[Schema]:
        """
        All (non-recursively nested) resources inside the given resource.
        """
