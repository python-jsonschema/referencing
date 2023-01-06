"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from typing import Any, Union

from referencing import Specification
from referencing.typing import URI, Mapping

#: A JSON Schema which is a JSON object
ObjectSchema = Mapping[str, Any]

#: A JSON Schema of any kind
Schema = Union[bool, ObjectSchema]


def _dollar_id(contents: Schema) -> URI | None:
    if isinstance(contents, bool):
        return
    return contents.get("$id")


def _legacy_id(contents: ObjectSchema) -> URI | None:
    return contents.get("id")


DRAFT202012 = Specification(id_of=_dollar_id)
DRAFT201909 = Specification(id_of=_dollar_id)
DRAFT7 = Specification(id_of=_dollar_id)
DRAFT6 = Specification(id_of=_dollar_id)
DRAFT4 = Specification(id_of=_legacy_id)
DRAFT3 = Specification(id_of=_legacy_id)


BY_ID: Mapping[URI, Specification[Any]] = {
    "https://json-schema.org/draft/2020-12/schema": DRAFT202012,
    "https://json-schema.org/draft/2019-09/schema": DRAFT201909,
    "http://json-schema.org/draft-07/schema#": DRAFT7,
    "http://json-schema.org/draft-06/schema#": DRAFT6,
    "http://json-schema.org/draft-04/schema#": DRAFT4,
    "http://json-schema.org/draft-03/schema#": DRAFT3,
}
