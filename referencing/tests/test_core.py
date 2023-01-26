import pytest

from referencing import Registry, Resource, Specification, exceptions
from referencing.jsonschema import DRAFT202012

ID_AND_CHILDREN = Specification(
    id_of=lambda contents: contents.get("ID"),
    subresources_of=lambda contents: contents.get("children", []),
)


class TestRegistry:
    def test_with_resource(self):
        """
        Adding a resource to the registry then allows re-retrieving it.
        """

        resource = Resource.opaque(contents={"foo": "bar"})
        uri = "urn:example"
        registry = Registry().with_resource(uri=uri, resource=resource)
        assert registry[uri] is resource

    def test_with_resources(self):
        """
        Adding multiple resources to the registry is like adding each one.
        """

        one = Resource.opaque(contents={})
        two = Resource(contents={"foo": "bar"}, specification=ID_AND_CHILDREN)
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

    def test_with_contents_from_json_schema(self):
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
        assert registry[uri] == Resource.opaque({"foo": "bar"})

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
        resource = Resource.opaque({"foo": "bar"})
        uri = "urn:example"
        registry = Registry({uri: resource}).crawl()
        assert registry[uri] is resource

    def test_crawl_finds_a_subresource(self):
        child_id = "urn:child"
        root = ID_AND_CHILDREN.create_resource(
            {"ID": "urn:root", "children": [{"ID": child_id, "foo": 12}]},
        )
        registry = Registry().with_resource(root.id(), root)
        with pytest.raises(LookupError):
            registry[child_id]

        expected = ID_AND_CHILDREN.create_resource({"ID": child_id, "foo": 12})
        assert registry.crawl()[child_id] == expected

    def test_contents(self):
        resource = Resource.opaque({"foo": "bar"})
        uri = "urn:example"
        registry = Registry().with_resources([(uri, resource)])
        assert registry.contents(uri) == {"foo": "bar"}

    def test_init(self):
        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        registry = Registry(
            {
                "http://example.com/1": one,
                "http://example.com/foo/bar": two,
            },
        )
        assert (
            registry
            == Registry()
            .with_resources(
                [
                    ("http://example.com/1", one),
                    ("http://example.com/foo/bar", two),
                ],
            )
            .crawl()
        )

    def test_dict_conversion(self):
        """
        Passing a `dict` to `Registry` gets converted to a `pmap`.

        So continuing to use the registry works.
        """

        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        registry = Registry(
            {"http://example.com/1": one},
        ).with_resources([("http://example.com/foo/bar", two)])
        assert (
            registry.crawl()
            == Registry()
            .with_resources(
                [
                    ("http://example.com/1", one),
                    ("http://example.com/foo/bar", two),
                ],
            )
            .crawl()
        )

    def test_combine(self):
        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        three = ID_AND_CHILDREN.create_resource({"baz": "quux"})

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

    def test_combine_with_uncrawled_resources(self):
        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        three = ID_AND_CHILDREN.create_resource({"baz": "quux"})

        first = Registry().with_resource("http://example.com/1", one)
        second = Registry().with_resource("http://example.com/foo/bar", two)
        third = Registry(
            {
                "http://example.com/1": one,
                "http://example.com/baz": three,
            },
        )
        expected = Registry(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
                ("http://example.com/baz", three),
            ],
        )
        combined = first.combine(second, third)
        assert combined != expected
        assert combined.crawl() == expected

    def test_repr(self):
        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        registry = Registry().with_resources(
            [
                ("http://example.com/1", one),
                ("http://example.com/foo/bar", two),
            ],
        )
        assert repr(registry) == "<Registry (2 uncrawled resources)>"
        assert repr(registry.crawl()) == "<Registry (2 resources)>"

    def test_repr_mixed_crawled(self):
        one = Resource.opaque(contents={})
        two = ID_AND_CHILDREN.create_resource({"foo": "bar"})
        registry = (
            Registry(
                {"http://example.com/1": one},
            )
            .crawl()
            .with_resource(uri="http://example.com/foo/bar", resource=two)
        )
        assert repr(registry) == "<Registry (2 resources, 1 uncrawled)>"

    def test_repr_one_resource(self):
        registry = Registry().with_resource(
            uri="http://example.com/1",
            resource=Resource.opaque(contents={}),
        )
        assert repr(registry) == "<Registry (1 uncrawled resource)>"

    def test_repr_empty(self):
        assert repr(Registry()) == "<Registry (0 resources)>"


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
        assert resource == Resource.opaque(contents={"foo": "bar"})

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
            default_specification=ID_AND_CHILDREN,
        )
        assert resource == Resource(
            contents=True,
            specification=ID_AND_CHILDREN,
        )

    def test_from_contents_with_fallback(self):
        resource = Resource.from_contents(
            {"foo": "bar"},
            default_specification=Specification.OPAQUE,
        )
        assert resource == Resource.opaque(contents={"foo": "bar"})

    def test_id_delegates_to_specification(self):
        specification = Specification(
            id_of=lambda contents: "urn:fixedID",
            subresources_of=lambda contents: [],
        )
        resource = Resource(
            contents={"foo": "baz"},
            specification=specification,
        )
        assert resource.id() == "urn:fixedID"

    def test_subresources_delegates_to_specification(self):
        resource = ID_AND_CHILDREN.create_resource({"children": [{}, 12]})
        assert list(resource.subresources()) == [
            ID_AND_CHILDREN.create_resource(each) for each in [{}, 12]
        ]

    def test_subresource_with_different_specification(self):
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema"}
        resource = ID_AND_CHILDREN.create_resource({"children": [schema]})
        assert list(resource.subresources()) == [
            DRAFT202012.create_resource(schema),
        ]

    def test_pointer_to_mapping(self):
        resource = Resource.opaque(contents={"foo": "baz"})
        resolver = Registry().resolver()
        assert resource.pointer("/foo", resolver=resolver).contents == "baz"

    def test_pointer_to_array(self):
        resource = Resource.opaque(contents={"foo": {"bar": [3]}})
        resolver = Registry().resolver()
        assert resource.pointer("/foo/bar/0", resolver=resolver).contents == 3

    def test_opaque(self):
        contents = {"foo": "bar"}
        assert Resource.opaque(contents) == Resource(
            contents=contents,
            specification=Specification.OPAQUE,
        )


class TestResolver:
    def test_lookup_exact_uri(self):
        resource = Resource.opaque(contents={"foo": "baz"})
        resolver = Registry({"http://example.com/1": resource}).resolver()
        resolved = resolver.lookup("http://example.com/1")
        assert resolved.contents == resource.contents

    def test_lookup_subresource(self):
        root = ID_AND_CHILDREN.create_resource(
            {
                "ID": "http://example.com/",
                "children": [
                    {"ID": "http://example.com/a", "foo": 12},
                ],
            },
        )
        resolver = Registry().with_resource(root.id(), root).resolver()
        resolved = resolver.lookup("http://example.com/a")
        assert resolved.contents == {"ID": "http://example.com/a", "foo": 12}

    def test_lookup_unknown_reference(self):
        resolver = Registry().resolver()
        ref = "http://example.com/does/not/exist"
        with pytest.raises(exceptions.Unresolvable) as e:
            resolver.lookup(ref)
        assert e.value == exceptions.Unresolvable(ref=ref)

    def test_lookup_non_existent_pointer(self):
        resource = Resource.opaque({"foo": {}})
        resolver = Registry({"http://example.com/1": resource}).resolver()
        ref = "http://example.com/1#/foo/bar"
        with pytest.raises(exceptions.Unresolvable) as e:
            resolver.lookup(ref)
        assert e.value == exceptions.Unresolvable(ref=ref)


class TestSpecification:
    def test_create_resource(self):
        specification = Specification(
            id_of=lambda contents: "urn:fixedID",
            subresources_of=lambda contents: [],
        )
        resource = specification.create_resource(contents={"foo": "baz"})
        assert resource == Resource(
            contents={"foo": "baz"},
            specification=specification,
        )
        assert resource.id() == "urn:fixedID"


class TestOpaqueSpecification:

    THINGS = [{"foo": "bar"}, True, 37, "foo", object()]

    @pytest.mark.parametrize("thing", THINGS)
    def test_no_id(self, thing):
        """
        An arbitrary thing has no ID.
        """

        assert Specification.OPAQUE.id_of(thing) is None

    @pytest.mark.parametrize("thing", THINGS)
    def test_no_subresources(self, thing):
        """
        An arbitrary thing has no subresources.
        """

        assert list(Specification.OPAQUE.subresources_of(thing)) == []


@pytest.mark.parametrize(
    "cls",
    [Registry, Resource, Specification],
)
def test_nonsubclassable(cls):
    with pytest.raises(Exception, match="(?i)subclassing"):  # noqa: B017

        class Boom(cls):  # pragma: no cover
            pass
