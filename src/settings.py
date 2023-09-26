from os.path import abspath, dirname

from jinja2 import Environment, PackageLoader

CLIENT_TEMPLATE_ROOT = dirname(dirname(abspath(__file__))) + "/src/client_template/"
TEMPLATES_ROOT = dirname(dirname(abspath(__file__))) + "/src/templates/"
CONSTANTS_ROOT = dirname(dirname(abspath(__file__))) + "/src/"
VERSION = "0.6.2"

templates = Environment(loader=PackageLoader("src", "templates"))
