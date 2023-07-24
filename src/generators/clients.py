from collections import defaultdict
from typing import Any, Dict, List
from urllib.parse import urlparse

from openapi_core import Spec
from rich.console import Console

from src.generators.schemas import SchemasGenerator
from src.utils import class_name_titled, clean_prop, get_func_name, get_type
from src.writer import write_to_client

console = Console()


class ClientsGenerator:
    """
    Handles all the content generated in the clients.py file.
    """

    results: Dict[str, int]
    spec: Spec
    output_dir: str
    schemas_generator: SchemasGenerator

    def __init__(
        self,
        spec: Spec,
        output_dir: str,
        schemas_generator: SchemasGenerator,
        asyncio: bool,
    ) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results = defaultdict(int)
        self.schemas_generator = schemas_generator
        self.asyncio = asyncio

    def generate_paths(self, api_url: str) -> None:
        for path in self.spec["paths"].items():
            self.write_path_to_client(api_url=api_url, path=path)
        console.log(f"Generated {self.results['get_methods']} GET methods...")
        console.log(f"Generated {self.results['post_methods']} POST methods...")

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
            if p.get("$ref"):
                # Not currently supporter
                continue
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
            for encoding, content in details.get("content", {}).items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    class_name = class_name_titled(
                        ref.replace("#/components/schemas/", "")
                    )
                elif title := content["schema"].get("title", False):
                    class_name = class_name_titled(title)
                else:
                    class_name = class_name_titled(encoding)
                response_classes.append(class_name)
        return list(set(response_classes))

    def get_input_class_names(self, inputs: Dict) -> List[str]:
        """
        Generates a list of input class for this operation.
        """
        input_classes = []
        for _, details in inputs.items():
            for encoding, content in details.get("content", {}).items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    class_name = class_name_titled(
                        ref.replace("#/components/schemas/", "")
                    )
                elif title := content["schema"].get("title", False):
                    class_name = title
                else:
                    # No idea, using the encoding?
                    class_name = encoding
                class_name = class_name_titled(class_name)
                input_classes.append(class_name)
        return list(set(input_classes))

    def generate_response_types(self, responses: Dict) -> str:
        response_class_names = self.get_response_class_names(responses=responses)
        if len(response_class_names) > 1:
            return f"""typing.Union[{', '.join([f'schemas.{r}' for r in response_class_names])}]"""
        elif len(response_class_names) == 0:
            return "None"
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
        elif len(input_class_names) == 0:
            return "None"
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
{self.asyncio and "async " or ""}def {func_name}({function_arguments['return_string']}) -> {response_types}:
    response = {self.asyncio and "await " or ""}http.get(f"{api_url}")
    return http.handle_response({func_name}, response)
    """
        self.results["get_methods"] += 1
        write_to_client(content=CONTENT, output_dir=self.output_dir)

    def generate_post_content(self, operation: Dict, api_url: str, path: str) -> None:
        api_url = f"{self.parse_api_base_url(api_url)}{path}"
        response_types = self.generate_response_types(operation["responses"])
        func_name = get_func_name(operation, path)
        if not operation.get("requestBody"):
            input_class_name = "None"
        else:
            input_class_name = self.generate_input_types(
                {"": operation.get("requestBody")}
            )
        function_arguments = self.generate_function_args(
            operation.get("parameters", [])
        )
        FUNCTION_ARGS = f"""
{function_arguments['return_string']}{function_arguments['return_string'] and ", "}data: {input_class_name}"""
        CONTENT = f"""
{self.asyncio and "async " or ""}def {func_name}({FUNCTION_ARGS}) -> {response_types}:
    response = {self.asyncio and "await " or ""}http.post(f"{api_url}", data=data and data.model_dump())
    return http.handle_response({func_name}, response)
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
