from __future__ import annotations

from collections.abc import Iterable, Sequence
from urllib.parse import unquote, urldefrag, urljoin

from attrs import evolve, field
from pyrsistent import m, plist, s
from pyrsistent.typing import PList, PMap, PSet

from referencing._attrs import define, frozen
from referencing.typing import Anchor as AnchorType, Schema, Specification


class UnidentifiedResource(Exception):
    pass


@frozen
class Anchor:

    name: str
    resource: Schema

    def resolve(self, resolver, uri) -> tuple[Schema, str]:
        return self.resource, uri


class OpaqueSpecification:
    """
    A non-specification `Specification` which treats resources opaquely.

    In particular, they have no subresources.
    """

    def id_of(self, resource):
        if resource is True or resource is False:
            return
        return resource.get("$id")  # REMOVEME

    def anchors_in(self, resource):
        return ()

    def subresources_of(self, resource):
        return ()


@frozen
class Registry:

    _contents: PMap[str, tuple[Schema, PMap[str, AnchorType]]] = field(
        default=m(),
        repr=lambda value: f"({len(value)} entries)",
    )
    _uncrawled: PSet[str] = field(default=s(), repr=False)
    _specification: Specification = OpaqueSpecification()

    def update(self, *registries: Registry) -> Registry:
        contents = (each._contents for each in registries)
        uncrawled = (each._uncrawled for each in registries)
        return evolve(
            self,
            contents=self._contents.update(*contents),
            uncrawled=self._uncrawled.update(*uncrawled),
        )

    def with_resource(self, resource) -> Registry:
        uri = self._specification.id_of(resource)
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

            id = self._specification.id_of(resource)
            if id is not None:
                contents = contents.set(id, (resource, m()))

            uncrawled = uncrawled.add(uri)
        return evolve(self, contents=contents, uncrawled=uncrawled)

    def with_anchors(
        self,
        uri: str,
        anchors: Iterable[AnchorType],
    ) -> Registry:
        assert uri.endswith("#") or "#" not in uri, uri
        resource, old = self._contents[uri]
        new = old.update({anchor.name: anchor for anchor in anchors})
        contents = self._contents.set(uri, (resource, new))
        return evolve(self, contents=contents)

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

            uri = urljoin(base_uri, self._specification.id_of(resource) or "")
            if uri != base_uri:
                registry = registry.with_identified_resource(
                    uri=uri,
                    resource=resource,
                )

            anchors = self._specification.anchors_in(resource)
            registry = registry.with_anchors(uri=uri, anchors=anchors)

            resources.extend(
                (uri, each)
                for each in self._specification.subresources_of(resource)
                if each is not True and each is not False
            )
        return evolve(registry, uncrawled=s())

    def resolver(self, root, specification) -> Resolver:
        uri = self._specification.id_of(root) or ""
        registry = self.with_identified_resource(uri=uri, resource=root)
        registry = evolve(registry, specification=specification)
        return Resolver(base_uri=uri, registry=registry)


@define
class Resolver:

    _base_uri: str
    _registry: Registry
    _previous: PList[Resolver] = field(default=plist(), repr=False)

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
            target, uri = anchor.resolve(resolver=self, uri=uri)

        id = self._registry._specification.id_of(target)
        if id is not None:
            base_uri = urljoin(self._base_uri, id)
        else:
            base_uri = uri
        return target, self.evolve(base_uri=base_uri, registry=registry)

    def with_root(self, root) -> Resolver:
        maybe_relative = self._registry._specification.id_of(root)
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
