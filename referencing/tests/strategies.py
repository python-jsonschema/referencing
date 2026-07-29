"""Hypothesis strategies for exercising registries and resources."""

from __future__ import annotations

from typing import Any

from hypothesis import strategies as st

from referencing import Registry, Resource

json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.text(),
    lambda children: (
        st.lists(children, max_size=3)
        | st.dictionaries(st.text(), children, max_size=3)
    ),
    max_leaves=10,
)
"""A strategy producing JSON-compatible values."""

uris = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",)),
    min_size=1,
    max_size=20,
).map(lambda path: f"urn:example:{path}")
"""A strategy producing non-empty opaque resource identifiers."""


@st.composite
def resources(draw: st.DrawFn) -> Resource[Any]:
    """Generate an opaque resource containing a JSON-compatible value."""
    return Resource.opaque(draw(json_values))


@st.composite
def registries(draw: st.DrawFn) -> Registry[Any]:
    """Generate a registry containing zero or more opaque resources."""
    pairs = draw(
        st.lists(
            st.tuples(uris, resources()),
            max_size=5,
            unique_by=lambda pair: pair[0],
        ),
    )
    return Registry().with_resources(pairs)
