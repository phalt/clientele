from distutils.dir_util import copy_tree
from typing import Dict, List
from urllib.parse import urlparse

from openapi_core import Spec

from src.settings import TEMPLATE_ROOT
from src.writer import write_to_client, write_to_response


class DataType:
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ONE_OF = "oneOf"
    ANY_OF = "anyOf"


def get_func_name(operation: Dict, path: str) -> str:
    if operation.get("operationId"):
        return operation["operationId"].split("__")[0]
    # Probably 3.0.1
    return path.replace("/", "_").replace("-", "_")[1:]


def get_type(t):
    t_type = t.get("type")
    if t_type == DataType.STRING:
        return "str"
    if t_type == DataType.INTEGER:
        return "int"
    if t_type == DataType.BOOLEAN:
        return "bool"
    if t_type == DataType.OBJECT:
        return "typing.Dict[str, typing.Any]"
    if t_type == DataType.ARRAY:
        return "typing.List[typing.Any]"
    if ref := t.get("$ref"):
        return f'"{ref.replace("#/components/schemas/", "")}"'
    return t_type


class SchemasGenerator:
    """
    Handles all the content generated in the responses.py file.
    """

    spec: Spec
    schemas: Dict[str, str]

    def __init__(self, spec: Spec) -> None:
        self.spec = spec
        self.schemas = {}

    generated_response_class_names: List[str] = []

    def generate_class_properties(self, properties: Dict) -> str:
        """
        Generate a string list of the properties for this pydantic class.
        """
        content = ""
        for arg, arg_details in properties.items():
            content = content + f"""    {arg}: {get_type(arg_details)}\n"""
        return content

    def generate_schema_classes(self, output_dir: str) -> None:
        """
        Generates the Pydantic response classes.
        """
        for schema_key, schema in self.spec["components"]["schemas"].items():
            enum = False
            if schema.get("enum"):
                enum = True
                properties = self.generate_class_properties(
                    {v: {"type": f'"{v}"'} for v in schema["enum"]}
                )
            else:
                properties = self.generate_class_properties(schema.get("properties"))
            self.schemas[schema_key] = properties
            content = f"""
class {schema_key}({"Enum" if enum else "BaseModel"}):
{properties}
    """
            write_to_response(
                content,
                output_dir=output_dir,
            )


class Generator:
    """
    Top-level generator.
    """

    spec: Spec
    asyncio: bool
    schemas_generator: SchemasGenerator

    def __init__(self, spec: Spec, asyncio: bool) -> None:
        self.schemas_generator = SchemasGenerator(spec=spec)
        self.spec = spec
        self.asyncio = asyncio

    def parse_api_base_url(self, url: str) -> str:
        """
        Returns the base API URL for this service
        """
        url_parts = urlparse(url=url)
        return f"{url_parts.scheme}://{url_parts.hostname}{f':{url_parts.port}' if url_parts.port not in [80, 443] else ''}"  # noqa

    def generate_function_args(self, parameters: List[Dict]) -> str:
        return_parameters = []
        for p in parameters:
            if p["required"]:
                return_parameters.append(f"{p['name']}: str")
            else:
                return_parameters.append(f"{p['name']}: typing.Optional[str]")
        return ", ".join(return_parameters)

    def get_response_class_names(self, responses: Dict) -> List[str]:
        """
        Generates a list of response class for this operation.
        """
        response_classes = []
        for _, details in responses.items():
            for _, content in details["content"].items():
                response_classes.append(
                    content["schema"]["$ref"].replace("#/components/schemas/", "")
                )
        return list(set(response_classes))

    def generate_response_types(self, responses: Dict) -> str:
        response_class_names = self.get_response_class_names(responses=responses)
        if len(response_class_names) > 1:
            return f"""typing.Union[{', '.join([f'schemas.{r}' for r in response_class_names])}]"""
        else:
            return f"schemas.{response_class_names[0]}"

    def generate_get_content(
        self, operation: Dict, output_dir: str, api_url: str, path: str
    ) -> None:
        api_url = f"{self.parse_api_base_url(api_url)}{path}"
        response_types = self.generate_response_types(operation["responses"])
        func_name = get_func_name(operation, path)
        CONTENT = f"""
def {func_name}({self.generate_function_args(operation.get('parameters', []))}) -> {response_types}:
    response = _get(f"{api_url}")
    return _handle_response({func_name}, response)
    """
        write_to_client(content=CONTENT, output_dir=output_dir)

    def generate_post_content(
        self, operation: Dict, output_dir: str, api_url: str, path: str
    ) -> None:
        api_url = f"{self.parse_api_base_url(api_url)}{path}"
        response_types = self.generate_response_types(operation["responses"])
        func_name = get_func_name(operation, path)
        input_class_name = self.generate_response_types({"": operation["requestBody"]})
        CONTENT = f"""
def {func_name}(data: {input_class_name}) -> {response_types}:
    response = _post(f"{api_url}", data=data.model_dump())
    return _handle_response({func_name}, response)
    """
        write_to_client(content=CONTENT, output_dir=output_dir)

    def write_path_to_client(self, api_url: str, path: Dict, output_dir: str) -> None:
        url, operations = path
        for method, operation in operations.items():
            if method == "get":
                self.generate_get_content(
                    operation=operation,
                    output_dir=output_dir,
                    api_url=api_url,
                    path=url,
                )
            elif method == "post":
                self.generate_post_content(
                    operation=operation,
                    output_dir=output_dir,
                    api_url=api_url,
                    path=url,
                )

    def generate(self, url: str, output_dir: str) -> None:
        copy_tree(src=TEMPLATE_ROOT, dst=output_dir)
        self.schemas_generator.generate_schema_classes(output_dir=output_dir)
        for path in self.spec["paths"].items():
            self.write_path_to_client(api_url=url, path=path, output_dir=output_dir)
