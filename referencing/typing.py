"""
Type-annotation related support for the referencing library.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, TypeVar

try:
    from collections.abc import Mapping as Mapping

    Mapping[str, str]
except TypeError:  # pragma: no cover
    from typing import Mapping as Mapping


if TYPE_CHECKING:
    from referencing._core import Resolved, Resolver

#: A URI which identifies a `Resource`.
URI = str

#: The type of documents within a registry.
D = TypeVar("D")


class Anchor(Protocol[D]):
    """
    An anchor within a `Resource`.

    Beyond "simple" anchors, some specifications like JSON Schema's 2020
    version have dynamic anchors.
    """

    @property
    def name(self) -> str:
        """
        Return the name of this anchor.
        """
        ...

    def resolve(self, resolver: Resolver[D]) -> Resolved[D]:
        """
        Return the resource for this anchor.
        """
        ...
