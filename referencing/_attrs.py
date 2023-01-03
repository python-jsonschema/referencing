from typing import TYPE_CHECKING, NoReturn

if TYPE_CHECKING:
    from attrs import define as define, frozen as frozen
else:
    from attrs import define as _define, frozen as _frozen

    def define(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return _define(cls)

    def frozen(cls):
        cls.__init_subclass__ = UnsupportedSubclassing.complain
        return _frozen(cls)


class UnsupportedSubclassing(Exception):
    @classmethod
    def complain(this) -> NoReturn:
        raise UnsupportedSubclassing(
            "Subclassing is not part of referencing's public API. "
            "If no other suitable API exists for what you're trying to do, "
            "feel free to file an issue asking for one.",
        )
