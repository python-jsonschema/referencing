"""
Errors, oh no!
"""
from typing import Any

import attrs

from referencing._attrs import frozen
from referencing.typing import URI


@frozen
class NoSuchResource(KeyError):
    """
    The given URI is not present in a registry.
    """

    ref: URI

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        return attrs.astuple(self) == attrs.astuple(other)


@frozen
class Unretrievable(KeyError):
    """
    The given URI is not present in a registry, and retrieving it failed.
    """

    ref: URI


@frozen
class CannotDetermineSpecification(Exception):
    """
    Attempting to detect the appropriate `Specification` failed.

    This happens if no discernible information is found in the contents of the
    new resource which would help identify it.
    """

    contents: Any


@attrs.frozen
class Unresolvable(Exception):
    """
    A reference was unresolvable.
    """

    ref: URI

    def __eq__(self, other: Any) -> bool:
        if self.__class__ is not other.__class__:
            return NotImplemented
        return attrs.astuple(self) == attrs.astuple(other)


@frozen
class PointerToNowhere(Unresolvable):
    """
    A JSON Pointer leads to a part of a document that does not exist.
    """

    resource: Any

    def __str__(self):
        return f"{self.ref!r} does not exist within {self.resource.contents!r}"


@frozen
class NoSuchAnchor(Unresolvable):
    """
    An anchor does not exist within a particular resource.
    """

    resource: Any
    anchor: str

    def __str__(self):
        return (
            f"{self.anchor!r} does not exist within {self.resource.contents!r}"
        )
