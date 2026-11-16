"""Typing contracts for the core mixins."""

from typing import Any, Callable, Protocol


class HasContext(Protocol):
    _ctx: int | None

    def _check_alive(self) -> None: ...

    def _call(self, function: Callable[..., Any], *args, with_context: bool = True) -> Any: ...
