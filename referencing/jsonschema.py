"""
Referencing implementations for JSON Schema specs (historic & current).
"""

from __future__ import annotations

from referencing import Specification

DRAFT202012 = Specification(id_of=lambda contents: None)
DRAFT201909 = Specification(id_of=lambda contents: None)
DRAFT7 = Specification(id_of=lambda contents: None)
DRAFT6 = Specification(id_of=lambda contents: None)
DRAFT4 = Specification(id_of=lambda contents: None)
DRAFT3 = Specification(id_of=lambda contents: None)


BY_ID = {
    "https://json-schema.org/draft/2020-12/schema": DRAFT202012,
    "https://json-schema.org/draft/2019-09/schema": DRAFT201909,
    "http://json-schema.org/draft-07/schema#": DRAFT7,
    "http://json-schema.org/draft-06/schema#": DRAFT6,
    "http://json-schema.org/draft-04/schema#": DRAFT4,
    "http://json-schema.org/draft-03/schema#": DRAFT3,
}
