"""
Type-annotation related support for the referencing library.
"""
from __future__ import annotations

from typing import TypeVar

try:
    from collections.abc import Mapping as Mapping

    Mapping[str, str]
except TypeError:  # pragma: no cover
    from typing import Mapping as Mapping

#: A URI which identifies a `Resource`.
URI = str

#: The type of documents within a registry.
D = TypeVar("D")
