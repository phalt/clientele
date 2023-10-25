from collections import defaultdict
from typing import Optional

from openapi_core import Spec
from pydantic import BaseModel
from rich.console import Console

from clientele.generators.standard import utils, writer
from clientele.generators.standard.generators import http, schemas

console = Console()


class ParametersResponse(BaseModel):
    # Parameters that need to be passed in the URL query
    query_args: dict[str, str]
    # Parameters that need to be passed as variables in the function
    path_args: dict[str, str]
    # Parameters that are needed in the headers object
    headers_args: dict[str, str]

    def get_path_args_as_string(self):
        # Get all the path arguments, and the query arguments and make a big string out of them.
        args = list(self.path_args.items()) + list(self.query_args.items())
        return ", ".join(f"{k}: {v}" for k, v in args)


class ClientsGenerator:
    """
    Handles all the content generated in the clients.py file.
    """

    method_template_map: dict[str, str]
    results: dict[str, int]
    spec: Spec
    output_dir: str
    schemas_generator: schemas.SchemasGenerator
    http_generator: http.HTTPGenerator

    def __init__(
        self,
        spec: Spec,
        output_dir: str,
        schemas_generator: schemas.SchemasGenerator,
        http_generator: http.HTTPGenerator,
        asyncio: bool,
    ) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results = defaultdict(int)
        self.schemas_generator = schemas_generator
        self.http_generator = http_generator
        self.asyncio = asyncio
        self.method_template_map = dict(
            get="get_method.jinja2",
            delete="get_method.jinja2",
            post="post_method.jinja2",
            put="post_method.jinja2",
        )

    def generate_paths(self) -> None:
        for path in self.spec["paths"].items():
            self.write_path_to_client(path=path)
        console.log(f"Generated {self.results['get']} GET methods...")
        console.log(f"Generated {self.results['post']} POST methods...")
        console.log(f"Generated {self.results['put']} PUT methods...")
        console.log(f"Generated {self.results['delete']} DELETE methods...")

    def generate_parameters(self, parameters: list[dict], additional_parameters: list[dict]) -> ParametersResponse:
        param_keys = []
        query_args = {}
        path_args = {}
        headers_args = {}
        all_parameters = parameters + additional_parameters
        for param in all_parameters:
            if param.get("$ref"):
                # Get the actual parameter it is referencing
                param = utils.get_param_from_ref(spec=self.spec, param=param)
            clean_key = utils.snake_case_prop(param["name"])
            if clean_key in param_keys:
                continue
            in_ = param.get("in")
            required = param.get("required", False) or in_ != "query"
            if in_ == "query":
                # URL query string values
                if required:
                    query_args[clean_key] = utils.get_type(param["schema"])
                else:
                    query_args[clean_key] = f"typing.Optional[{utils.get_type(param['schema'])}]"
            elif in_ == "path":
                # Function arguments
                if required:
                    path_args[clean_key] = utils.get_type(param["schema"])
                else:
                    path_args[clean_key] = f"typing.Optional[{utils.get_type(param['schema'])}]"
            elif in_ == "header":
                # Header object arguments
                headers_args[param["name"]] = utils.get_type(param["schema"])
            param_keys.append(clean_key)
        return ParametersResponse(
            query_args=query_args,
            path_args=path_args,
            headers_args=headers_args,
        )

    def get_response_class_names(self, responses: dict, func_name: str) -> list[str]:
        """
        Generates a list of response class for this operation.
        For each response found, also generate the schema by calling
        the schema generator.
        Returns a list of names of the classes generated.
        """
        status_code_map: dict[str, str] = {}
        response_classes = []
        for status_code, details in responses.items():
            for _, content in details.get("content", {}).items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    # An object reference, so should be generated
                    # by the schema generator later.
                    class_name = utils.class_name_titled(utils.schema_ref(ref))
                elif title := content["schema"].get("title", False):
                    # This usually means we have an object that isn't
                    # $ref so we need to create the schema class here
                    class_name = utils.class_name_titled(title)
                    self.schemas_generator.make_schema_class(class_name, schema=content["schema"])
                else:
                    # At this point we're just making things up!
                    # It is likely it isn't an object it is just a simple resonse.
                    class_name = utils.class_name_titled(func_name + status_code + "Response")
                    # We need to generate the class at this point because it does not exist
                    self.schemas_generator.make_schema_class(
                        func_name + status_code + "Response",
                        schema={"properties": {"test": content["schema"]}},
                    )
                status_code_map[status_code] = class_name
                response_classes.append(class_name)
        self.http_generator.add_status_codes_to_bundle(func_name=func_name, status_code_map=status_code_map)
        return sorted(list(set(response_classes)))

    def get_input_class_names(self, inputs: dict) -> list[str]:
        """
        Generates a list of input class for this operation.
        """
        input_classes = []
        for _, details in inputs.items():
            for encoding, content in details.get("content", {}).items():
                class_name = ""
                if ref := content["schema"].get("$ref", False):
                    class_name = utils.class_name_titled(utils.schema_ref(ref))
                elif title := content["schema"].get("title", False):
                    class_name = title
                else:
                    # No idea, using the encoding?
                    class_name = encoding
                class_name = utils.class_name_titled(class_name)
                input_classes.append(class_name)
        return list(set(input_classes))

    def generate_response_types(self, responses: dict, func_name: str) -> str:
        response_class_names = self.get_response_class_names(responses=responses, func_name=func_name)
        if len(response_class_names) > 1:
            return utils.union_for_py_ver([f"schemas.{r}" for r in response_class_names])
        elif len(response_class_names) == 0:
            return "None"
        else:
            return f"schemas.{response_class_names[0]}"

    def generate_input_types(self, request_body: dict) -> str:
        input_class_names = self.get_input_class_names(inputs={"": request_body})
        for input_class in input_class_names:
            if input_class not in self.schemas_generator.schemas.keys():
                # It doesn't exist! Generate the schema for it
                self.schemas_generator.generate_input_class(schema=request_body)
        if len(input_class_names) > 1:
            return utils.union_for_py_ver([f"schemas.{r}" for r in input_class_names])
        elif len(input_class_names) == 0:
            return "None"
        else:
            return f"schemas.{input_class_names[0]}"

    def generate_function(
        self,
        operation: dict,
        method: str,
        url: str,
        additional_parameters: list[dict],
        summary: Optional[str],
    ):
        func_name = utils.get_func_name(operation, url)
        response_types = self.generate_response_types(responses=operation["responses"], func_name=func_name)
        function_arguments = self.generate_parameters(
            parameters=operation.get("parameters", []),
            additional_parameters=additional_parameters,
        )
        if query_args := function_arguments.query_args:
            api_url = url + utils.create_query_args(list(query_args.keys()))
        else:
            api_url = url
        if method in ["post", "put"] and not operation.get("requestBody"):
            data_class_name = "None"
        elif method in ["post", "put"]:
            data_class_name = self.generate_input_types(operation.get("requestBody", {}))
        else:
            data_class_name = None
        self.results[method] += 1
        template = writer.templates.get_template(self.method_template_map[method])
        if headers := function_arguments.headers_args:
            header_class_name = self.schemas_generator.generate_headers_class(
                properties=headers,
                func_name=func_name,
            )
        else:
            header_class_name = None
        content = template.render(
            asyncio=self.asyncio,
            func_name=func_name,
            function_arguments=function_arguments.get_path_args_as_string(),
            response_types=response_types,
            data_class_name=data_class_name,
            header_class_name=header_class_name,
            api_url=api_url,
            method=method,
            summary=operation.get("summary", summary),
        )
        writer.write_to_client(content=content, output_dir=self.output_dir)

    def write_path_to_client(self, path: dict) -> None:
        url, operations = path
        for method, operation in operations.items():
            if method.lower() in self.method_template_map.keys():
                self.generate_function(
                    operation=operation,
                    method=method,
                    url=url,
                    additional_parameters=operations.get("parameters", []),
                    summary=operations.get("summary", None),
                )
