from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterable, Protocol, Union

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
    @property
    def name(self) -> str:
        ...

    def resolve(
        self,
        resolver: Resolver,
        uri: str,
    ) -> tuple[IdentifiedResource, str]:
        pass


class Specification(Protocol):
    def id_of(self, resource: Schema) -> str | None:
        """
        The URI ID of the given resource.
        """

    def anchors_in(self, resource: ObjectSchema) -> Iterable[Anchor]:
        """
        All (non-recursively nested) anchors inside the given resource.
        """

    def subresources_of(self, resource: ObjectSchema) -> Iterable[Schema]:
        """
        All (non-recursively nested) resources inside the given resource.
        """
