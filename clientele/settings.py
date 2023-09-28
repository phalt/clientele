from os.path import abspath, dirname

from jinja2 import Environment, PackageLoader

CLIENT_TEMPLATE_ROOT = (
    dirname(dirname(abspath(__file__))) + "/clientele/client_template/"
)
TEMPLATES_ROOT = dirname(dirname(abspath(__file__))) + "/clientele/templates/"
CONSTANTS_ROOT = dirname(dirname(abspath(__file__))) + "/clientele/"
VERSION = "0.6.3"

templates = Environment(loader=PackageLoader("clientele", "templates"))
