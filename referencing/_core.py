from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, Union
from urllib.parse import unquote, urldefrag, urljoin

from pyrsistent import m
from pyrsistent.typing import PMap
import attrs

try:
    Mapping[str, str]
except TypeError:
    from typing import Mapping


class UnsupportedSubclassing(Exception):
    @classmethod
    def complain(this):
        raise UnsupportedSubclassing(
            "Subclassing is not part of referencing's public API. "
            "If no other suitable API exists for what you're trying to do, "
            "feel free to file an issue asking for one.",
        )


class UnidentifiedResource(Exception):
    pass


if TYPE_CHECKING:
    from attrs import define, frozen
else:

    def define(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return attrs.define(cls)

    def frozen(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return attrs.frozen(cls)


Schema = Union[bool, Mapping[str, Any]]


@frozen
class Anchor:

    uri: str
    name: str
    resource: Schema

    def added_to(self, registry: Registry):
        return registry.with_anchor(
            uri=self.uri,
            anchor=self.name,
            resource=self.resource,
        )


@frozen
class DynamicAnchor:

    uri: str
    name: str
    resource: Schema

    def added_to(self, registry: Registry):
        return registry.with_anchor(
            uri=self.uri,
            anchor=self.name,
            resource=self.resource,
        )


@frozen
class IdentifiedResource:

    uri: str
    resource: Schema

    def added_to(self, registry: Registry):
        return registry.with_identified_resource(
            uri=self.uri,
            resource=self.resource,
        )


@frozen
class Registry:

    _contents: PMap[str, tuple[Schema, PMap[str, Schema]]] = attrs.field(
        default=m(),
        repr=lambda value: f"({len(value)} entries)",
    )

    def resource_at(self, uri):
        return self._contents[uri]

    def with_resource(self, resource):
        uri = id_of(resource)
        if uri is None:
            raise UnidentifiedResource(resource)
        return self.with_identified_resource(uri=uri, resource=resource)

    def with_identified_resource(self, uri, resource):
        return self.with_resources([(uri, resource)])

    def update(self, *registries: Registry):
        contents = (registry._contents for registry in registries)
        return attrs.evolve(self, contents=self._contents.update(*contents))

    def with_resources(self, pairs):
        contents = self._contents
        for uri, resource in pairs:
            assert (
                uri == ""
                or uri not in self._contents
                or self._contents[uri][0] == resource
            ), (uri, self._contents[uri], resource)
            contents = contents.set(uri, (resource, m()))

            id = id_of(resource)
            if id is not None:
                contents = contents.set(id, (resource, m()))
        return attrs.evolve(self, contents=contents)

    def with_anchor(self, uri, anchor, resource):
        uri_resource, anchors = self._contents[uri]
        new = uri_resource, anchors.set(anchor, resource)
        return attrs.evolve(self, contents=self._contents.set(uri, new))

    def resolver(self, root) -> Resolver:
        uri = id_of(root) or ""
        registry = self.with_identified_resource(uri=uri, resource=root)
        return Resolver(base_uri=uri, registry=registry)

    def has_not_crawled(self, uri):
        at_uri = self._contents.get(uri)
        return at_uri is None or not at_uri[1]


@define
class Resolver:

    _base_uri: str
    _registry: Registry

    def lookup(self, ref: str):
        if ref.startswith("#"):
            uri, fragment = self._base_uri, ref[1:]
        else:
            uri, fragment = urldefrag(urljoin(self._base_uri, ref))
        if self._registry.has_not_crawled(uri):
            root, _ = self._registry.resource_at(self._base_uri)
            for each in find_subresources(base_uri=self._base_uri, root=root):
                self._registry = each.added_to(self._registry)

        resource, anchors = self._registry.resource_at(uri)
        target = resource
        if fragment.startswith("/"):
            segments = unquote(fragment[1:]).split("/")
            for segment in segments:
                if isinstance(target, Sequence):
                    segment = int(segment)  # type: ignore
                else:
                    segment = segment.replace("~1", "/").replace("~0", "~")
                target = target[segment]
        elif fragment:
            target = anchors[fragment]

        return target, self.with_base_uri(uri)

    def with_base_uri(self, base_uri):
        return attrs.evolve(self, base_uri=base_uri)

    def with_root(self, root) -> Resolver:
        maybe_relative = id_of(root)
        if maybe_relative is None:
            uri, registry = self._base_uri, self._registry
        else:
            uri = urljoin(self._base_uri, maybe_relative)
            registry = self._registry.with_identified_resource(
                uri=uri,
                resource=root,
            )
        return attrs.evolve(self, base_uri=uri, registry=registry)


SUBRESOURCE = {"items", "not"}
SUBRESOURCE_ITEMS = {"allOf"}
SUBRESOURCE_VALUES = {"$defs", "properties"}


def id_of(resource) -> str | None:
    if resource is True or resource is False:
        return None
    return resource.get("$id")


def find_subresources(
    root: Schema,
    base_uri: str,
) -> Iterable[Anchor | DynamicAnchor | IdentifiedResource]:
    resources = [(base_uri, root)]
    while resources:
        base_uri, resource = resources.pop()
        if resource is True or resource is False:
            continue

        uri = urljoin(base_uri, resource.get("$id", ""))
        if uri != base_uri:
            yield IdentifiedResource(uri=uri, resource=resource)

        anchor = resource.get("$anchor")
        if anchor is not None:
            yield Anchor(uri=uri, name=anchor, resource=resource)

        dynamic_anchor = resource.get("$dynamicAnchor")
        if dynamic_anchor is not None:
            yield DynamicAnchor(
                uri=uri,
                name=dynamic_anchor,
                resource=resource,
            )

        resources.extend(  # TODO: delay finding anchors in subresources...
            (uri, resource[k]) for k in SUBRESOURCE if k in resource
        )
        resources.extend(
            (uri, subresource)
            for k in SUBRESOURCE_VALUES
            if k in resource
            for subresource in resource[k].values()
        )
        resources.extend(  # TODO: delay finding anchors in subresources...
            (uri, subresource)
            for k in SUBRESOURCE_ITEMS
            if k in resource
            for subresource in resource[k]
        )
