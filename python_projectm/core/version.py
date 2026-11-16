from python_projectm.native import bindings as native


def get_version_string() -> str:
    return native.pypm_get_version_string().decode("utf-8")


def get_vcs_version_string() -> str:
    return native.pypm_get_vcs_version_string().decode("utf-8")
