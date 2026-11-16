class NativeError(RuntimeError):
    """Base error for native ProjectM bindings."""


class NativeLibraryNotFound(NativeError):
    """Raised when pypm_capi library cannot be found."""


class NativeSymbolError(NativeError):
    """Raised when a required symbol is missing in the library."""
