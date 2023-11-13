"""
Tests for (and via) referencing's Hypothesis support.
"""

from hypothesis import given, strategies

from referencing import Resource, Specification


@given(strategies.builds(Resource, specification=Specification.OPAQUE))
def test_opaque_resources_do_not_have_ids(resource):
    print(resource)
