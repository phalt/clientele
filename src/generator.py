from distutils.dir_util import copy_tree
from os.path import abspath, dirname
from urllib.parse import urlparse

from openapi_parser.specification import Path, Specification

TEMPLATE_ROOT = dirname(dirname(abspath(__file__))) + "/src/template/"


def parse_api_base_url(url: str) -> str:
    """
    Returns the base API URL for this service
    """
    url_parts = urlparse(url=url)
    return f"{url_parts.scheme}://{url_parts.hostname}{f':{url_parts.port}' if url_parts.port not in [80, 443] else ''}"


def generate_response_types(test: str) -> str:
    return """Union[ResponseHere]"""


def generate_response_classes() -> str:
    return """
    
@attrs.define
ResponseHere:
    status: str
"""

def write_path_to_client(api_url: str, path: Path) -> None:
    for operation in path.operations:
        operation_content = f"""
{generate_response_classes()}
def {operation.operation_id}(generate_args: str) -> {generate_response_types(test="test")}:
    return _get("{parse_api_base_url(api_url)}{path.url}")
"""
    print(operation_content)
    print(operation.responses)


def generate(url: str, specification: Specification, output_dir: str) -> None:
    copy_tree(src=TEMPLATE_ROOT, dst=output_dir)
    write_path_to_client(api_url=url, path=specification.paths[0])
