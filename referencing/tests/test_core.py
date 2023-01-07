import pytest

from referencing import Registry, Resource, Specification, exceptions
from referencing.jsonschema import DRAFT202012


class TestRegistry:
    def test_with_resource(self):
        """
        Adding a resource to the registry then allows re-retrieving it.
        """

        resource = Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )
        uri = "urn:example"
        registry = Registry().with_resource(uri=uri, resource=resource)
        assert registry[uri] is resource

    def test_with_resources(self):
        """
        Adding multiple resources to the registry is like adding each one.
        """

        one = Resource(contents={}, specification=Specification.OPAQUE)
        two = Resource(contents={"foo": "bar"}, specification=DRAFT202012)
        registry = Registry().with_resources(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
            ],
        )
        assert registry == Registry().with_resource(
            uri="http://example.com/1",
            resource=one,
        ).with_resource(
            uri="http://example.com/foo/bar",
            resource=two,
        )

    def test_with_contents(self):
        uri = "urn:example"
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        registry = Registry().with_contents([(uri, schema)])

        expected = Resource(contents=schema, specification=DRAFT202012)
        assert registry[uri] == expected

    def test_with_contents_and_default_specification(self):
        uri = "urn:example"
        registry = Registry().with_contents(
            [(uri, {"foo": "bar"})],
            default_specification=Specification.OPAQUE,
        )
        expected = Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )
        assert registry[uri] == expected

    def test_len(self):
        total = 5
        registry = Registry().with_contents(
            [(str(i), {"foo": "bar"}) for i in range(total)],
            default_specification=Specification.OPAQUE,
        )
        assert len(registry) == total

    def test_iter(self):
        registry = Registry().with_contents(
            [(str(i), {"foo": "bar"}) for i in range(8)],
            default_specification=Specification.OPAQUE,
        )
        assert set(registry) == {str(i) for i in range(8)}

    def test_crawl_still_has_top_level_resource(self):
        resource = Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )
        uri = "urn:example"
        registry = Registry().with_resources([(uri, resource)]).crawl()
        assert registry[uri] is resource

    def test_contents(self):
        resource = Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )
        uri = "urn:example"
        registry = Registry().with_resources([(uri, resource)])
        assert registry.contents(uri) == {"foo": "bar"}

    def test_init(self):
        one = Resource(contents={}, specification=Specification.OPAQUE)
        two = Resource(contents={"foo": "bar"}, specification=DRAFT202012)
        registry = Registry(
            {
                "http://example.com/1": one,
                "http://example.com/foo/bar": two,
            },
        )
        assert registry == Registry().with_resources(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
            ],
        )

    def test_dict_conversion(self):
        """
        Passing a `dict` to `Registry` gets converted to a `pmap`.

        So continuing to use the registry works.
        """

        one = Resource(contents={}, specification=Specification.OPAQUE)
        two = Resource(contents={"foo": "bar"}, specification=DRAFT202012)
        registry = Registry(
            {"http://example.com/1": one},
        ).with_resources([("http://example.com/foo/bar", two)])
        assert registry == Registry().with_resources(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
            ],
        )

    def test_combine(self):
        one = Resource(contents={}, specification=Specification.OPAQUE)
        two = Resource(contents={"foo": "bar"}, specification=DRAFT202012)
        three = Resource(contents={"baz": "quux"}, specification=DRAFT202012)

        first = Registry({"http://example.com/1": one})
        second = Registry({"http://example.com/foo/bar": two})
        third = Registry(
            {
                "http://example.com/1": one,
                "http://example.com/baz": three,
            },
        )
        assert first.combine(second, third) == Registry(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
                ("http://example.com/baz", three),
            ],
        )


class TestResource:
    def test_from_contents_from_json_schema(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        resource = Resource.from_contents(schema)
        assert resource == Resource(contents=schema, specification=DRAFT202012)

    def test_from_contents_with_no_discernible_information(self):
        """
        Creating a resource with no discernible way to see what
        specification it belongs to (e.g. no ``$schema`` keyword for JSON
        Schema) raises an error.
        """

        with pytest.raises(exceptions.CannotDetermineSpecification):
            Resource.from_contents({"foo": "bar"})

    def test_from_contents_with_no_discernible_information_and_default(self):
        resource = Resource.from_contents(
            {"foo": "bar"},
            default_specification=Specification.OPAQUE,
        )
        assert resource == Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )

    def test_from_contents_unneeded_default(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        resource = Resource.from_contents(
            schema,
            default_specification=Specification.OPAQUE,
        )
        assert resource == Resource(
            contents=schema,
            specification=DRAFT202012,
        )

    def test_non_mapping_from_contents(self):
        resource = Resource.from_contents(
            True,
            default_specification=Specification.OPAQUE,
        )
        assert resource == Resource(
            contents=True,
            specification=Specification.OPAQUE,
        )

    def test_from_contents_with_fallback(self):
        resource = Resource.from_contents(
            {"foo": "bar"},
            default_specification=Specification.OPAQUE,
        )
        assert resource == Resource(
            contents={"foo": "bar"},
            specification=Specification.OPAQUE,
        )

    def test_id_delegates_to_specification(self):
        specification = Specification(id_of=lambda contents: "urn:fixedID")
        resource = Resource(
            contents={"foo": "baz"},
            specification=specification,
        )
        assert resource.id() == "urn:fixedID"


class TestResolver:
    def test_lookup_exact_uri(self):
        resource = Resource(
            contents={"foo": "baz"},
            specification=Specification.OPAQUE,
        )
        resolver = Registry({"http://example.com/1": resource}).resolver()
        resolved = resolver.lookup("http://example.com/1")
        assert resolved.contents == resource.contents


class TestSpecification:
    def test_create_resource(self):
        specification = Specification(id_of=lambda contents: "urn:fixedID")
        resource = specification.create_resource(contents={"foo": "baz"})
        assert resource == Resource(
            contents={"foo": "baz"},
            specification=specification,
        )
        assert resource.id() == "urn:fixedID"


class TestOpaqueSpecification:
    @pytest.mark.parametrize(
        "thing",
        [{"foo": "bar"}, True, 37, "foo", object()],
    )
    def test_no_id(self, thing):
        """
        An arbitrary thing has no ID.
        """

        assert Specification.OPAQUE.id_of(thing) is None


@pytest.mark.parametrize(
    "cls",
    [Registry, Resource, Specification],
)
def test_nonsubclassable(cls):
    with pytest.raises(Exception):

        class Boom(cls):  # pragma: no cover
            pass
