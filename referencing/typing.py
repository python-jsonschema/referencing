from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Union

try:
    from collections.abc import Mapping

    Mapping[str, str]
except TypeError:
    from typing import Mapping

if TYPE_CHECKING:
    from referencing._core import IdentifiedResource, Resolver


#: A JSON Schema which is a JSON object
ObjectSchema = Mapping[str, Any]

#: A JSON Schema of any kind
Schema = Union[bool, ObjectSchema]


class Anchor(Protocol):
    """
    An anchor within a `Schema`.

    Beyond "simple" anchors, some specifications like JSON Schema's 2020
    version have dynamic anchors.
    """

    @property
    def name(self) -> str:
        ...

    def resolve(
        self,
        resolver: Resolver,
        uri: str,
    ) -> tuple[IdentifiedResource, str]:
        pass
