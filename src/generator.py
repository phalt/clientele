from collections import defaultdict
from distutils.dir_util import copy_tree
from typing import Any, Dict, List
from urllib.parse import urlparse

from openapi_core import Spec
from rich.console import Console

from src.settings import TEMPLATE_ROOT
from src.writer import write_to_client, write_to_response

console = Console()


class DataType:
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    ONE_OF = "oneOf"
    ANY_OF = "anyOf"


def class_name_titled(input_str: str) -> str:
    """
    Make the input string suitable for a class name
    """
    input_str = input_str.title()
    for badstr in [".", "-", "_", ">", "<"]:
        input_str = input_str.replace(badstr, "")
    return input_str


def clean_prop(input_str: str) -> str:
    """
    Clean a property to not have invalid characters
    """
    for dropchar in [">", "<"]:
        input_str = input_str.replace(dropchar, "")
    for badstr in ["-", "."]:
        input_str = input_str.replace(badstr, "_")
    reserved_words = ["from"]
    if input_str in reserved_words:
        input_str = input_str + "_"
    return input_str


def get_func_name(operation: Dict, path: str) -> str:
    if operation.get("operationId"):
        return operation["operationId"].split("__")[0]
    # Probably 3.0.1
    return path.replace("/", "_").replace("-", "_")[1:]


def get_type(t):
    t_type = t.get("type")
    if t_type == DataType.STRING:
        return "str"
    if t_type in [DataType.INTEGER, DataType.NUMBER]:
        return "int"
    if t_type == DataType.BOOLEAN:
        return "bool"
    if t_type == DataType.OBJECT:
        return "typing.Dict[str, typing.Any]"
    if t_type == DataType.ARRAY:
        return "typing.List[typing.Any]"
    if ref := t.get("$ref"):
        return f'"{class_name_titled(ref.replace("#/components/schemas/", ""))}"'
    if t_type is None:
        # In this case, make it an "Any"
        return "typing.Any"
    return t_type


class SchemasGenerator:
    """
    Handles all the content generated in the responses.py file.
    """

    spec: Spec
    schemas: Dict[str, str]
    output_dir: str

    def __init__(self, spec: Spec, output_dir: str) -> None:
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir

    generated_response_class_names: List[str] = []

    def generate_enum_properties(self, properties: Dict) -> str:
        """
        Generate a string list of the properties for this enum.
        """
        content = ""
        for arg, arg_details in properties.items():
            content = (
                content
                + f"""    {clean_prop(arg.upper())} = {get_type(arg_details)}\n"""
            )
        return content

    def generate_class_properties(self, properties: Dict) -> str:
        """
        Generate a string list of the properties for this pydantic class.
        """
        content = ""
        for arg, arg_details in properties.items():
            arg_type = get_type(arg_details)
            # TODO support this
            is_optional = False
            content = (
                content
                + f"""    {clean_prop(arg)}: {is_optional and f"typing.Optional[{arg_type}]" or arg_type}\n"""
            )
        return content

    def generate_input_class(self, schema: Dict) -> None:
        for _, schema_details in schema.items():
            content = schema_details["content"]
            for encoding, input_schema in content.items():
                class_name = ""
                if ref := input_schema["schema"].get("$ref", False):
                    class_name = class_name_titled(
                        ref.replace("#/components/schemas/", "")
                    )
                elif title := input_schema["schema"].get("title", False):
                    class_name = title
                else:
                    raise "Cannot find a name for this class"
                properties = self.generate_class_properties(
                    input_schema["schema"]["properties"]
                )
                content = f"""
class {class_name}(BaseModel):
{properties if properties else "    pass"}
    """
            write_to_response(
                content,
                output_dir=self.output_dir,
            )

    def generate_schema_classes(self) -> None:
        """
        Generates the Pydantic response classes.
        """
        for schema_key, schema in self.spec["components"]["schemas"].items():
            schema_key = class_name_titled(schema_key)
            enum = False
            if schema.get("enum"):
                enum = True
                properties = self.generate_enum_properties(
                    {v: {"type": f'"{v}"'} for v in schema["enum"]}
                )
            else:
                properties = self.generate_class_properties(schema.get("properties", {}))
            self.schemas[schema_key] = properties
            content = f"""
class {schema_key}({"Enum" if enum else "BaseModel"}):
{properties if properties else "    pass"}
    """
            write_to_response(
                content,
                output_dir=self.output_dir,
            )

        console.log(f"Generated {len(self.schemas.items())} schemas...")


class Generator:
    """
    Top-level generator.
    """

    spec: Spec
    asyncio: bool
    schemas_generator: SchemasGenerator
    output_dir: str
    results: Dict[str, int]

    def __init__(self, spec: Spec, output_dir: str, asyncio: bool) -> None:
        self.schemas_generator = SchemasGenerator(spec=spec, output_dir=output_dir)
        self.spec = spec
        self.asyncio = asyncio
        self.output_dir = output_dir
        self.results = defaultdict(int)

    def parse_api_base_url(self, url: str) -> str:
        """
        Returns the base API URL for this service
        """
        url_parts = urlparse(url=url)
        return f"{url_parts.scheme}://{url_parts.hostname}{f':{url_parts.port}' if url_parts.port not in [80, 443] else ''}"  # noqa

    def generate_function_args(self, parameters: List[Dict]) -> Dict[str, Any]:
        return_string_bits = []
        param_keys = []
        query_args = []
        path_args = []
        for p in parameters:
            clean_key = clean_prop(p["name"])
            if clean_key in param_keys:
                continue
            in_ = p.get("in")
            required = p.get("required", False) or in_ != "query"
            if in_ == "query":
                query_args.append(p["name"])
            elif in_ == "path":
                path_args.append(p["name"])
            if required:
                return_string_bits.append(f"{clean_key}: {get_type(p['schema'])}")
            else:
                return_string_bits.append(
                    f"{clean_key}: typing.Optional[{get_type(p['schema'])}]"
                )
            param_keys.append(clean_key)
        return_string = ", ".join(return_string_bits)
        return {
            "return_string": return_string,
            "query_args": query_args,
            "path_args": path_args,
        }

    def get_response_class_names(self, responses: Dict) -> List[str]:
        """
        Generates a list of response class for this operation.
        """
        response_classes = []
        for _, details in responses.items():
            for _, content in details["content"].items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    class_name = class_name_titled(
                        ref.replace("#/components/schemas/", "")
                    )
                elif title := content["schema"].get("title", False):
                    class_name = title
                else:
                    raise "Cannot find a name for this class"
                response_classes.append(class_name)
        return list(set(response_classes))

    def get_input_class_names(self, inputs: Dict) -> List[str]:
        """
        Generates a list of input class for this operation.
        """
        input_classes = []
        for _, details in inputs.items():
            for _, content in details["content"].items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    class_name = class_name_titled(
                        ref.replace("#/components/schemas/", "")
                    )
                elif title := content["schema"].get("title", False):
                    class_name = title
                else:
                    breakpoint()
                    raise "Cannot find a name for this class"
                input_classes.append(class_name)
        return list(set(input_classes))

    def generate_response_types(self, responses: Dict) -> str:
        response_class_names = self.get_response_class_names(responses=responses)
        if len(response_class_names) > 1:
            return f"""typing.Union[{', '.join([f'schemas.{r}' for r in response_class_names])}]"""
        else:
            return f"schemas.{response_class_names[0]}"

    def generate_input_types(self, request_body: Dict) -> str:
        input_class_names = self.get_input_class_names(inputs=request_body)
        for input_class in input_class_names:
            if input_class not in self.schemas_generator.schemas.keys():
                # It doesn't exist! Generate the schema for it
                self.schemas_generator.generate_input_class(schema=request_body)
        if len(input_class_names) > 1:
            return f"""typing.Union[{', '.join([f'schemas.{r}' for r in input_class_names])}]"""
        else:
            return f"schemas.{input_class_names[0]}"

    def generate_get_content(self, operation: Dict, api_url: str, path: str) -> None:
        response_types = self.generate_response_types(operation["responses"])
        func_name = get_func_name(operation, path)
        function_arguments = self.generate_function_args(
            operation.get("parameters", [])
        )
        if query_args := function_arguments["query_args"]:
            api_url = f"{self.parse_api_base_url(api_url)}{path}"
            # TODO do this far more elegantly
            api_url = (
                api_url + "?" + "&".join([f"{p}=" + "{" + p + "}" for p in query_args])
            )
        else:
            api_url = f"{self.parse_api_base_url(api_url)}{path}"
        CONTENT = f"""
def {func_name}({function_arguments['return_string']}) -> {response_types}:
    response = _get(f"{api_url}")
    return _handle_response({func_name}, response)
    """
        self.results["get_methods"] += 1
        write_to_client(content=CONTENT, output_dir=self.output_dir)

    def generate_post_content(self, operation: Dict, api_url: str, path: str) -> None:
        api_url = f"{self.parse_api_base_url(api_url)}{path}"
        response_types = self.generate_response_types(operation["responses"])
        func_name = get_func_name(operation, path)
        input_class_name = self.generate_input_types({"": operation["requestBody"]})
        function_arguments = self.generate_function_args(
            operation.get("parameters", [])
        )
        FUNCTION_ARGS = f"""
{function_arguments['return_string']}{function_arguments['return_string'] and ", "}data: {input_class_name}"""
        CONTENT = f"""
def {func_name}({FUNCTION_ARGS}) -> {response_types}:
    response = _post(f"{api_url}", data=data.model_dump())
    return _handle_response({func_name}, response)
    """
        self.results["post_methods"] += 1
        write_to_client(content=CONTENT, output_dir=self.output_dir)

    def write_path_to_client(self, api_url: str, path: Dict) -> None:
        url, operations = path
        if servers := operations.get("servers"):
            api_url = servers[0]["url"]
        for method, operation in operations.items():
            if method == "get":
                self.generate_get_content(
                    operation=operation,
                    api_url=api_url,
                    path=url,
                )
            elif method == "post":
                self.generate_post_content(
                    operation=operation,
                    api_url=api_url,
                    path=url,
                )

    def generate(
        self,
        url: str,
    ) -> None:
        copy_tree(src=TEMPLATE_ROOT, dst=self.output_dir)
        self.schemas_generator.generate_schema_classes()
        for path in self.spec["paths"].items():
            self.write_path_to_client(api_url=url, path=path)
        # TODO: Generate security schemeas here
        console.log(f"Wrote {self.results['get_methods']} GET methods...")
        console.log(f"Wrote {self.results['post_methods']} POST methods...")
