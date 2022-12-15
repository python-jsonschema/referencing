from __future__ import annotations

from typing import Any, Iterable, Protocol, Union

try:
    from collections.abc import Mapping

    Mapping[str, str]
except TypeError:
    from typing import Mapping


ObjectSchema = Mapping[str, Any]
Schema = Union[bool, ObjectSchema]


class Anchor(Protocol):
    @property
    def uri(self) -> str:
        ...

    @property
    def name(self) -> str:
        ...

    def resolve(
        self,
        dynamic_scope: Iterable[tuple[Schema, Anchor]],
        uri: str,
    ) -> tuple[Schema, str]:
        pass


class Specification(Protocol):
    def subresources_of(self, resource: ObjectSchema) -> Iterable[Schema]:
        """
        All (non-recursively nested) resources inside the given resource.
        """
