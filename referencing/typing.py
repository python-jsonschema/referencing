from __future__ import annotations

try:
    from collections.abc import Mapping

    Mapping[str, str]
except TypeError:
    from typing import Mapping
