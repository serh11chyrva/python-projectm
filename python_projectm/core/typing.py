from typing import Protocol

from python_projectm.native.bindings import ContextHandle


class HasContext(Protocol):
    """
    Typing-only protocol for classes that own a ProjectM native context.
    """

    _ctx: ContextHandle
