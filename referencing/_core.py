from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING, Any, Union
from urllib.parse import unquote, urldefrag, urljoin

from pyrsistent import m, plist, s
from pyrsistent.typing import PList, PMap, PSet

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
    from attrs import define, evolve, field, frozen
else:
    from attrs import define as _define, evolve, field, frozen as _frozen

    def define(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return _define(cls)

    def frozen(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return _frozen(cls)


Schema = Union[bool, Mapping[str, Any]]


@frozen
class Anchor:

    uri: str
    name: str
    resource: Schema

    def resolve(self, dynamic_scope, uri) -> tuple[Schema, str]:
        return self.resource, uri


@frozen
class DynamicAnchor:

    uri: str
    name: str
    resource: Schema

    def resolve(self, dynamic_scope, uri) -> tuple[Schema, str]:
        last = self.resource
        for resource, anchors in dynamic_scope:
            anchor = anchors.get(self.name)
            if isinstance(anchor, DynamicAnchor):
                last = anchor.resource
            elif "$ref" not in resource:
                break
        return last, id_of(last) or ""  # FIXME: consider when this can be None


AnchorType = Union[Anchor, DynamicAnchor]


@frozen
class Registry:

    _contents: PMap[str, tuple[Schema, PMap[str, AnchorType]]] = field(
        default=m(),
        repr=lambda value: f"({len(value)} entries)",
    )
    _uncrawled: PSet[str] = field(default=s())

    def update(self, *registries: Registry) -> Registry:
        contents = (each._contents for each in registries)
        uncrawled = (each._uncrawled for each in registries)
        return evolve(
            self,
            contents=self._contents.update(*contents),
            uncrawled=self._uncrawled.update(*uncrawled),
        )

    def with_resource(self, resource) -> Registry:
        uri = id_of(resource)
        if uri is None:
            raise UnidentifiedResource(resource)
        return self.with_identified_resource(uri=uri, resource=resource)

    def with_identified_resource(self, uri, resource) -> Registry:
        return self.with_resources([(uri, resource)])

    def with_resources(self, pairs) -> Registry:
        uncrawled = self._uncrawled
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

            uncrawled = uncrawled.add(uri)
        return evolve(self, contents=contents, uncrawled=uncrawled)

    def with_anchor(self, anchor: Anchor | DynamicAnchor) -> Registry:
        resource, anchors = self._contents[anchor.uri]
        new = resource, anchors.set(anchor.name, anchor)
        return evolve(self, contents=self._contents.set(anchor.uri, new))

    def resource_at(self, uri: str) -> tuple[Schema, Registry]:
        at_uri = self._contents.get(uri)
        if at_uri is not None and at_uri[1]:
            registry = self
        else:
            registry = self._crawl()
        return registry._contents[uri][0], registry

    def anchors_at(self, uri) -> PMap[str, AnchorType]:
        return self._contents[uri][1]

    def _crawl(self) -> Registry:
        registry = self
        resources = [(uri, self._contents[uri][0]) for uri in self._uncrawled]
        while resources:
            base_uri, resource = resources.pop()
            if resource is True or resource is False:
                continue

            uri = urljoin(base_uri, resource.get("$id", ""))
            if uri != base_uri:
                registry = registry.with_identified_resource(
                    uri=uri,
                    resource=resource,
                )

            anchor = resource.get("$anchor")
            if anchor is not None:
                registry = registry.with_anchor(
                    Anchor(uri=uri, name=anchor, resource=resource),
                )

            dynamic_anchor = resource.get("$dynamicAnchor")
            if dynamic_anchor is not None:
                registry = registry.with_anchor(
                    DynamicAnchor(
                        uri=uri,
                        name=dynamic_anchor,
                        resource=resource,
                    ),
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
            resources.extend(
                (uri, subresource)
                for k in SUBRESOURCE_ITEMS
                if k in resource
                for subresource in resource[k]
            )
        return evolve(registry, uncrawled=s())

    def resolver(self, root) -> Resolver:
        uri = id_of(root) or ""
        registry = self.with_identified_resource(uri=uri, resource=root)
        return Resolver(base_uri=uri, registry=registry)


@define
class Resolver:

    _base_uri: str
    _registry: Registry
    _previous: PList[Resolver] = plist()

    def lookup(self, ref: str) -> tuple[Schema, Resolver]:
        if ref.startswith("#"):
            uri, fragment = self._base_uri, ref[1:]
        else:
            uri, fragment = urldefrag(urljoin(self._base_uri, ref))
        target, registry = self._registry.resource_at(uri)
        if fragment.startswith("/"):
            segments = unquote(fragment[1:]).split("/")
            for segment in segments:
                if isinstance(target, Sequence):
                    segment = int(segment)  # type: ignore
                else:
                    segment = segment.replace("~1", "/").replace("~0", "~")
                target = target[segment]  # type: ignore # this can't be a bool
        elif fragment:
            anchor = registry.anchors_at(uri=uri)[fragment]
            target, uri = anchor.resolve(
                dynamic_scope=self.dynamic_scope(),
                uri=uri,
            )

        return target, self.evolve(base_uri=uri, registry=registry)

    def with_root(self, root) -> Resolver:
        maybe_relative = id_of(root)
        if maybe_relative is None:
            return self

        uri = urljoin(self._base_uri, maybe_relative)
        registry = self._registry.with_identified_resource(
            uri=uri,
            resource=root,
        )
        return self.evolve(base_uri=uri, registry=registry)

    def evolve(self, **kwargs):
        previous = self._previous.cons(self._base_uri)
        return evolve(self, previous=previous, **kwargs)

    def dynamic_scope(self):
        for uri in self._previous:
            resource, _ = self._registry.resource_at(uri)
            yield resource, self._registry.anchors_at(uri)


SUBRESOURCE = {"items", "not"}
SUBRESOURCE_ITEMS = {"allOf"}
SUBRESOURCE_VALUES = {"$defs", "properties"}


def id_of(resource) -> str | None:
    if resource is True or resource is False:
        return None
    return resource.get("$id")
