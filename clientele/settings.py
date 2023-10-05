import platform
from os.path import abspath, dirname

from jinja2 import Environment, PackageLoader

TEMPLATES_ROOT = dirname(dirname(abspath(__file__))) + "/clientele/templates/"
VERSION = "0.7.0"

templates = Environment(loader=PackageLoader("clientele", "templates"))


def split_ver():
    return [int(v) for v in platform.python_version().split(".")]


PY_VERSION = split_ver()
