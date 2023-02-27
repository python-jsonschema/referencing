"""
Helpers for the retrieval of resources off of a local filesystem.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import os

from referencing import Resource, exceptions
from referencing.typing import URI, D, Retrieve


def retriever(
    root: os.PathLike[Any] | str,
    load: Callable[[Path], D] = lambda path: json.loads(path.read_text()),
) -> Retrieve[D]:
    r"""
    Create a retriever which looks for resources on the filesystem.

    Suitable for passing to `Registry`\ 's ``retrieve`` argument.

    Does not allow retrieving resources outside the provided root directory.
    """
    _root = Path(root)

    def retrieve(uri: URI):
        path = _root / uri
        try:
            path.relative_to(_root)
        except ValueError:
            raise exceptions.Unretrievable(ref=uri)
        return Resource.from_contents(load(path))  # type: ignore[reportGeneralTypeIssues]  # noqa: E501

    return retrieve
