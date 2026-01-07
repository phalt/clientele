import platform

VERSION = "1.4.2"


def split_ver():
    return [int(v) for v in platform.python_version().split(".")]


PY_VERSION = split_ver()
