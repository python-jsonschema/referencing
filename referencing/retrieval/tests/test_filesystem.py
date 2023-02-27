import json

import pytest

from referencing import Registry, exceptions
from referencing.retrieval import filesystem

SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "integer",
}


def test_file(tmp_path):
    tmp_path.joinpath("foo.json").write_text(json.dumps(SCHEMA))

    retrieve = filesystem.retriever(root=tmp_path)
    registry = Registry(retrieve=retrieve)

    retrieved = registry.get_or_retrieve("foo.json")
    assert retrieved.value.contents == SCHEMA


def test_nested_file(tmp_path):
    baz = tmp_path / "bar/baz"
    baz.mkdir(parents=True)
    baz.joinpath("quux.json").write_text(json.dumps(SCHEMA))

    retrieve = filesystem.retriever(root=tmp_path)
    registry = Registry(retrieve=retrieve)

    retrieved = registry.get_or_retrieve("bar/baz/quux.json")
    assert retrieved.value.contents == SCHEMA


def test_custom_loader(tmp_path):
    as_json = json.dumps(SCHEMA)
    tmp_path.joinpath("foo.json").write_text(as_json)
    tmp_path.joinpath("foo.reversed.json").write_text(as_json[::-1])

    retrieve = filesystem.retriever(
        root=tmp_path,
        load=lambda path: (
            json.loads(path.read_text()[::-1])
            if path.name.endswith(".reversed.json")
            else json.loads(path.read_text())
        ),
    )
    registry = Registry(retrieve=retrieve)

    retrieved = registry.get_or_retrieve("foo.json")
    assert retrieved.value.contents == SCHEMA


def test_unsuccessful_retrieval(tmp_path):
    retrieve = filesystem.retriever(root=tmp_path)
    registry = Registry(retrieve=retrieve)
    with pytest.raises(exceptions.Unretrievable):
        registry.get_or_retrieve("boom.json")


def test_outside_root_dir(tmp_path):
    secret = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "very": "secret",
        "password": 37,
    }
    path = tmp_path.joinpath("secrets.json")
    path.write_text(json.dumps(secret))

    child = tmp_path / "child"
    child.mkdir()

    retrieve = filesystem.retriever(root=child)

    registry = Registry(retrieve=retrieve)
    with pytest.raises(exceptions.Unretrievable):
        registry.get_or_retrieve(str(path))
