from typing import NoReturn

# Yak stack:
#   - PyCQA/pylint#6006
#   - python/mypy#5406
from attrs import define as _define, frozen as _frozen


def define(cls):
    cls.__init_subclass__ = _do_not_subclass
    return _define(cls)


def frozen(cls):
    cls.__init_subclass__ = _do_not_subclass
    return _frozen(cls)


class UnsupportedSubclassing(Exception):
    pass


def _do_not_subclass() -> NoReturn:
    raise UnsupportedSubclassing(
        "Subclassing is not part of referencing's public API. "
        "If no other suitable API exists for what you're trying to do, "
        "feel free to file an issue asking for one.",
    )
