"""Validation shared by the core and rendering adapters."""

import math
import operator


def integer(value, name: str, *, minimum: int = 1, maximum: int = 2**31 - 1) -> int:
    """Return an integer in the inclusive bounds, rejecting booleans and floats."""
    if isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    try:
        result = operator.index(value)
    except TypeError as error:
        raise TypeError(f"{name} must be an integer") from error
    if not minimum <= result <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return result


def dimensions(width, height, *, allow_zero: bool = False) -> tuple[int, int]:
    """Validate integer dimensions, optionally allowing zero to suspend rendering."""
    minimum = 0 if allow_zero else 1
    return integer(width, "width", minimum=minimum), integer(height, "height", minimum=minimum)


def nonnegative(value) -> float:
    """Convert a value to a finite, nonnegative float."""
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Value must be finite and nonnegative")
    return result


def encoded_text(value: str, name: str) -> bytes:
    """Encode a string as UTF-8, rejecting embedded NUL characters."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if "\0" in value:
        raise ValueError(f"{name} must not contain a NUL character")
    return value.encode("utf-8")
