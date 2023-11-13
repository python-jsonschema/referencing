"""
A plugin for making referencing objects usable within Hypothesis.

This module is meant to be used as an entry point, meaning it should
automatically be imported if both referencing and hypothesis are being used.

See https://hypothesis.readthedocs.io/en/latest/strategies.html#hypothesis-integration-via-setuptools-entry-points
and/or https://hatch.pypa.io/latest/config/metadata/#entry-points for further
details.
"""

from typing import Callable, TypeVar

from hypothesis import strategies

from referencing import Resource

contents = strategies.integers()

T = TypeVar("T")


def register(cls: type[T]):
    def _register(strategy: Callable[[], T]):
        strategies.register_type_strategy(cls, strategy)
        return strategy

    return _register


@register(Resource)
def resource():
    return contents
