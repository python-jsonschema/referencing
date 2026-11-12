import pytest

from referencing import Registry, Resource, Specification
import referencing.jsonschema


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "https://json-schema.org/draft/2020-12/schema",
            referencing.jsonschema.DRAFT202012,
        ),
        (
            "https://json-schema.org/draft/2019-09/schema",
            referencing.jsonschema.DRAFT201909,
        ),
        (
            "http://json-schema.org/draft-07/schema#",
            referencing.jsonschema.DRAFT7,
        ),
        (
            "http://json-schema.org/draft-06/schema#",
            referencing.jsonschema.DRAFT6,
        ),
        (
            "http://json-schema.org/draft-04/schema#",
            referencing.jsonschema.DRAFT4,
        ),
        (
            "http://json-schema.org/draft-03/schema#",
            referencing.jsonschema.DRAFT3,
        ),
    ],
)
def test_schemas_with_explicit_schema_keywords_are_detected(uri, expected):
    """
    The $schema keyword in JSON Schema is a dialect identifier.
    """
    contents = {"$schema": uri}
    resource = Resource.from_contents(contents)
    assert resource == Resource(contents=contents, specification=expected)


def test_unknown_dialect():
    dialect_id = "http://example.com/unknown-json-schema-dialect-id"
    with pytest.raises(referencing.jsonschema.UnknownDialect) as excinfo:
        Resource.from_contents({"$schema": dialect_id})
    assert excinfo.value.uri == dialect_id


@pytest.mark.parametrize(
    "id, specification",
    [
        ("$id", referencing.jsonschema.DRAFT202012),
        ("$id", referencing.jsonschema.DRAFT201909),
        ("$id", referencing.jsonschema.DRAFT7),
        ("$id", referencing.jsonschema.DRAFT6),
        ("id", referencing.jsonschema.DRAFT4),
        ("id", referencing.jsonschema.DRAFT3),
    ],
)
def test_id_of_mapping(id, specification):
    uri = "http://example.com/some-schema"
    assert specification.id_of({id: uri}) == uri


@pytest.mark.parametrize(
    "specification",
    [
        referencing.jsonschema.DRAFT202012,
        referencing.jsonschema.DRAFT201909,
        referencing.jsonschema.DRAFT7,
        referencing.jsonschema.DRAFT6,
    ],
)
@pytest.mark.parametrize("value", [True, False])
def test_id_of_bool(specification, value):
    assert specification.id_of(value) is None


@pytest.mark.parametrize(
    "specification",
    [
        referencing.jsonschema.DRAFT202012,
        referencing.jsonschema.DRAFT201909,
        referencing.jsonschema.DRAFT7,
        referencing.jsonschema.DRAFT6,
    ],
)
@pytest.mark.parametrize("value", [True, False])
def test_anchors_in_bool(specification, value):
    assert list(specification.anchors_in(value)) == []


@pytest.mark.parametrize(
    "specification",
    [
        referencing.jsonschema.DRAFT202012,
        referencing.jsonschema.DRAFT201909,
        referencing.jsonschema.DRAFT7,
        referencing.jsonschema.DRAFT6,
    ],
)
@pytest.mark.parametrize("value", [True, False])
def test_subresources_of_bool(specification, value):
    assert list(specification.subresources_of(value)) == []


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "https://json-schema.org/draft/2020-12/schema",
            referencing.jsonschema.DRAFT202012,
        ),
        (
            "https://json-schema.org/draft/2019-09/schema",
            referencing.jsonschema.DRAFT201909,
        ),
        (
            "http://json-schema.org/draft-07/schema#",
            referencing.jsonschema.DRAFT7,
        ),
        (
            "http://json-schema.org/draft-06/schema#",
            referencing.jsonschema.DRAFT6,
        ),
        (
            "http://json-schema.org/draft-04/schema#",
            referencing.jsonschema.DRAFT4,
        ),
        (
            "http://json-schema.org/draft-03/schema#",
            referencing.jsonschema.DRAFT3,
        ),
    ],
)
def test_specification_with(uri, expected):
    assert referencing.jsonschema.specification_with(uri) == expected


@pytest.mark.parametrize(
    "uri, expected",
    [
        (
            "http://json-schema.org/draft-07/schema",
            referencing.jsonschema.DRAFT7,
        ),
        (
            "http://json-schema.org/draft-06/schema",
            referencing.jsonschema.DRAFT6,
        ),
        (
            "http://json-schema.org/draft-04/schema",
            referencing.jsonschema.DRAFT4,
        ),
        (
            "http://json-schema.org/draft-03/schema",
            referencing.jsonschema.DRAFT3,
        ),
    ],
)
def test_specification_with_no_empty_fragment(uri, expected):
    assert referencing.jsonschema.specification_with(uri) == expected


def test_specification_with_unknown_dialect():
    dialect_id = "http://example.com/unknown-json-schema-dialect-id"
    with pytest.raises(referencing.jsonschema.UnknownDialect) as excinfo:
        referencing.jsonschema.specification_with(dialect_id)
    assert excinfo.value.uri == dialect_id


def test_specification_with_default():
    dialect_id = "http://example.com/unknown-json-schema-dialect-id"
    specification = referencing.jsonschema.specification_with(
        dialect_id,
        default=Specification.OPAQUE,
    )
    assert specification is Specification.OPAQUE


# FIXME: The tests below should move to the referencing suite but I haven't yet
#        figured out how to represent dynamic (& recursive) ref lookups in it.
def test_lookup_trivial_dynamic_ref():
    one = referencing.jsonschema.DRAFT202012.create_resource(
        {"$dynamicAnchor": "foo"},
    )
    resolver = Registry().with_resource("http://example.com", one).resolver()
    resolved = resolver.lookup("http://example.com#foo")
    assert resolved.contents == one.contents


def test_multiple_lookup_trivial_dynamic_ref():
    TRUE = referencing.jsonschema.DRAFT202012.create_resource(True)
    root = referencing.jsonschema.DRAFT202012.create_resource(
        {
            "$id": "http://example.com",
            "$dynamicAnchor": "fooAnchor",
            "$defs": {
                "foo": {
                    "$id": "foo",
                    "$dynamicAnchor": "fooAnchor",
                    "$defs": {
                        "bar": True,
                        "baz": {
                            "$dynamicAnchor": "fooAnchor",
                        },
                    },
                },
            },
        },
    )
    resolver = (
        Registry()
        .with_resources(
            [
                ("http://example.com", root),
                ("http://example.com/foo/", TRUE),
                ("http://example.com/foo/bar", root),
            ],
        )
        .resolver()
    )

    first = resolver.lookup("http://example.com")
    second = first.resolver.lookup("foo/")
    resolver = second.resolver.lookup("bar").resolver
    fourth = resolver.lookup("#fooAnchor")
    assert fourth.contents == root.contents


def test_dynamic_anchor_uses_matching_scope_uri_for_followup_lookup():
    """
    A dynamic override also supplies the base for relative follow-up refs.

    The two public lookup paths deliberately have different dynamic scopes:
    looking up ``A#x`` from ``Cam`` starts at ``Cam``, while entering ``A``
    first makes ``A`` the nearest scope for a later ``#x`` lookup.
    """
    a = {
        "$id": "https://example.test/A",
        "$dynamicAnchor": "x",
        "$defs": {
            "y": {"$dynamicAnchor": "y", "const": "A.y"},
        },
    }
    cam = {
        "$id": "https://example.test/Cam",
        "$defs": {"x": {"$dynamicAnchor": "x", "const": "Cam.x"}},
    }
    b = {
        "$id": "https://example.test/B",
        "$dynamicAnchor": "y",
        "const": "B.y",
    }
    registry = Registry().with_resources(
        [
            (a["$id"], referencing.jsonschema.DRAFT202012.create_resource(a)),
            (
                cam["$id"],
                referencing.jsonschema.DRAFT202012.create_resource(cam),
            ),
            (b["$id"], referencing.jsonschema.DRAFT202012.create_resource(b)),
        ],
    )
    caller = registry.resolver(base_uri="https://example.test/Cam")

    foreign = caller.lookup("https://example.test/A#x")
    entered = caller.lookup("https://example.test/A")
    current = entered.resolver.lookup("#x")

    assert foreign.contents["const"] == "Cam.x"
    assert current.contents["const"] == "Cam.x"
    assert (
        foreign.resolver.lookup("https://example.test/B#y").contents["const"]
        == "B.y"
    )
    assert (
        current.resolver.lookup("https://example.test/B#y").contents["const"]
        == "A.y"
    )
    assert foreign.resolver._base_uri == "https://example.test/Cam"
    assert current.resolver._base_uri == "https://example.test/Cam"
    assert (
        next(iter(foreign.resolver.dynamic_scope()))[0]
        == "https://example.test/Cam"
    )
    assert [uri for uri, _ in current.resolver.dynamic_scope()] == [
        "https://example.test/A",
        "https://example.test/Cam",
    ]
    for resolved, expected_scope in (
        (foreign, ["https://example.test/Cam"]),
        (
            current,
            [
                "https://example.test/Cam",
                "https://example.test/A",
                "https://example.test/Cam",
            ],
        ),
    ):
        third = resolved.resolver.lookup("#x")
        fourth = third.resolver.lookup("#x")
        assert [uri for uri, _ in fourth.resolver.dynamic_scope()] == (
            expected_scope
        )


def test_dynamic_anchor_nested_override_uses_camera_resource_for_pointer():
    base_uri = "https://example.test/base.json"
    camera_uri = "https://example.test/camera.json"
    base = referencing.jsonschema.DRAFT202012.create_resource(
        {
            "$id": base_uri,
            "$dynamicAnchor": "concreteData",
        },
    )
    camera = referencing.jsonschema.DRAFT202012.create_resource(
        {
            "$id": camera_uri,
            "$ref": base_uri,
            "$defs": {
                "override": {"$dynamicAnchor": "concreteData"},
                "size": {"type": "integer"},
            },
        },
    )
    registry = Registry().with_resources(
        [(base_uri, base), (camera_uri, camera)],
    )

    entered = registry.resolver(base_uri=camera_uri).lookup(base_uri)
    override = entered.resolver.lookup("#concreteData")
    size = override.resolver.lookup("#/$defs/size")

    assert size.contents == {"type": "integer"}
    assert override.resolver._base_uri == camera_uri


def test_dynamic_anchor_relative_id_does_not_join_against_target_uri():
    base_uri = "https://example.test/base/root.json"
    camera_uri = "https://example.test/camera/dir/root.json"
    override_seed_uri = "https://example.test/camera/dir/override.json"
    override_uri = "https://example.test/camera/override.json"
    base = referencing.jsonschema.DRAFT202012.create_resource(
        {"$id": base_uri, "$dynamicAnchor": "x"},
    )
    override = referencing.jsonschema.DRAFT202012.create_resource(
        {"$id": "../override.json", "$dynamicAnchor": "x"},
    )
    camera = referencing.jsonschema.DRAFT202012.create_resource({})
    registry = Registry().with_resources(
        [
            (base_uri, base),
            (camera_uri, camera),
            (override_seed_uri, override),
        ],
    )

    entered_override = registry.resolver(base_uri=camera_uri).lookup(
        "../override.json",
    )
    entered_base = entered_override.resolver.lookup(base_uri)
    resolved = entered_base.resolver.lookup("#x")

    assert resolved.resolver._base_uri == override_uri


def test_dynamic_anchor_without_match_keeps_subresource_base():
    resource = referencing.jsonschema.DRAFT202012.create_resource(
        {"$id": "https://example.test/root", "$dynamicAnchor": "x"},
    )
    resolver = (
        Registry()
        .with_resource(
            "https://example.test/root",
            resource,
        )
        .resolver()
    )

    resolved = resolver.lookup("https://example.test/root#x")

    assert resolved.resolver._base_uri == "https://example.test/root"


def test_multiple_lookup_dynamic_ref_to_nondynamic_ref():
    one = referencing.jsonschema.DRAFT202012.create_resource(
        {"$anchor": "fooAnchor"},
    )
    two = referencing.jsonschema.DRAFT202012.create_resource(
        {
            "$id": "http://example.com",
            "$dynamicAnchor": "fooAnchor",
            "$defs": {
                "foo": {
                    "$id": "foo",
                    "$dynamicAnchor": "fooAnchor",
                    "$defs": {
                        "bar": True,
                        "baz": {
                            "$dynamicAnchor": "fooAnchor",
                        },
                    },
                },
            },
        },
    )
    resolver = (
        Registry()
        .with_resources(
            [
                ("http://example.com", two),
                ("http://example.com/foo/", one),
                ("http://example.com/foo/bar", two),
            ],
        )
        .resolver()
    )

    first = resolver.lookup("http://example.com")
    second = first.resolver.lookup("foo/")
    resolver = second.resolver.lookup("bar").resolver
    fourth = resolver.lookup("#fooAnchor")
    assert fourth.contents == two.contents


def test_lookup_trivial_recursive_ref():
    one = referencing.jsonschema.DRAFT201909.create_resource(
        {"$recursiveAnchor": True},
    )
    resolver = Registry().with_resource("http://example.com", one).resolver()
    first = resolver.lookup("http://example.com")
    resolved = referencing.jsonschema.lookup_recursive_ref(
        resolver=first.resolver,
    )
    assert resolved.contents == one.contents


def test_lookup_recursive_ref_to_bool():
    TRUE = referencing.jsonschema.DRAFT201909.create_resource(True)
    registry = Registry({"http://example.com": TRUE})
    resolved = referencing.jsonschema.lookup_recursive_ref(
        resolver=registry.resolver(base_uri="http://example.com"),
    )
    assert resolved.contents == TRUE.contents


def test_multiple_lookup_recursive_ref_to_bool():
    TRUE = referencing.jsonschema.DRAFT201909.create_resource(True)
    root = referencing.jsonschema.DRAFT201909.create_resource(
        {
            "$id": "http://example.com",
            "$recursiveAnchor": True,
            "$defs": {
                "foo": {
                    "$id": "foo",
                    "$recursiveAnchor": True,
                    "$defs": {
                        "bar": True,
                        "baz": {
                            "$recursiveAnchor": True,
                            "$anchor": "fooAnchor",
                        },
                    },
                },
            },
        },
    )
    resolver = (
        Registry()
        .with_resources(
            [
                ("http://example.com", root),
                ("http://example.com/foo/", TRUE),
                ("http://example.com/foo/bar", root),
            ],
        )
        .resolver()
    )

    first = resolver.lookup("http://example.com")
    second = first.resolver.lookup("foo/")
    resolver = second.resolver.lookup("bar").resolver
    fourth = referencing.jsonschema.lookup_recursive_ref(resolver=resolver)
    assert fourth.contents == root.contents


def test_multiple_lookup_recursive_ref_with_nonrecursive_ref():
    one = referencing.jsonschema.DRAFT201909.create_resource(
        {"$recursiveAnchor": True},
    )
    two = referencing.jsonschema.DRAFT201909.create_resource(
        {
            "$id": "http://example.com",
            "$recursiveAnchor": True,
            "$defs": {
                "foo": {
                    "$id": "foo",
                    "$recursiveAnchor": True,
                    "$defs": {
                        "bar": True,
                        "baz": {
                            "$recursiveAnchor": True,
                            "$anchor": "fooAnchor",
                        },
                    },
                },
            },
        },
    )
    three = referencing.jsonschema.DRAFT201909.create_resource(
        {"$recursiveAnchor": False},
    )
    resolver = (
        Registry()
        .with_resources(
            [
                ("http://example.com", three),
                ("http://example.com/foo/", two),
                ("http://example.com/foo/bar", one),
            ],
        )
        .resolver()
    )

    first = resolver.lookup("http://example.com")
    second = first.resolver.lookup("foo/")
    resolver = second.resolver.lookup("bar").resolver
    fourth = referencing.jsonschema.lookup_recursive_ref(resolver=resolver)
    assert fourth.contents == two.contents


def test_empty_registry():
    assert referencing.jsonschema.EMPTY_REGISTRY == Registry()
