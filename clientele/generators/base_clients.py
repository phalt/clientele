"""Base class for client generators shared by standard and classbase generators."""

import collections
import typing

import pydantic
from cicerone.spec import openapi_spec as cicerone_openapi_spec
from rich import console as rich_console

from clientele.generators import cicerone_compat
from clientele.generators.standard import utils

console = rich_console.Console()


class ParametersResponse(pydantic.BaseModel):
    # Parameters that need to be passed in the URL query
    query_args: dict[str, str]
    # Parameters that need to be passed as variables in the function
    path_args: dict[str, str]
    # Parameters that are needed in the headers object
    headers_args: dict[str, str]
    # Mapping from sanitized Python name to original API parameter name
    param_name_map: dict[str, str] = {}

    def get_path_args_as_string(self) -> str:
        # Get all the path arguments, and the query arguments and make a big string out of them.
        args = list(self.path_args.items()) + list(self.query_args.items())
        # Separate required and optional parameters
        # Python requires all required parameters (no default) before optional ones (with default)
        required_args = []
        optional_args = []
        for k, v in args:
            if v.startswith("typing.Optional["):
                optional_args.append(f"{k}: {v} = None")
            else:
                required_args.append(f"{k}: {v}")
        # Return required parameters first, then optional ones
        return ", ".join(required_args + optional_args)

    def get_required_args_as_string(self) -> str:
        """Get only required parameters (those without Optional wrapper)."""
        args = list(self.path_args.items()) + list(self.query_args.items())
        required_args = []
        for k, v in args:
            if not v.startswith("typing.Optional["):
                required_args.append(f"{k}: {v}")
        return ", ".join(required_args) if required_args else ""

    def get_optional_args_as_string(self) -> str:
        """Get only optional parameters (those with Optional wrapper)."""
        args = list(self.path_args.items()) + list(self.query_args.items())
        optional_args = []
        for k, v in args:
            if v.startswith("typing.Optional["):
                optional_args.append(f"{k}: {v} = None")
        return ", ".join(optional_args) if optional_args else ""

    def get_required_path_args_as_string(self) -> str:
        """Get only required path parameters (for clientele-api generator)."""
        required_args = []
        for k, v in self.path_args.items():
            if not v.startswith("typing.Optional["):
                required_args.append(f"{k}: {v}")
        return ", ".join(required_args) if required_args else ""

    def has_query_args(self) -> bool:
        """Check if there are any query parameters."""
        return len(self.query_args) > 0


class BaseClientsGenerator:
    """
    Base class for generating client code from OpenAPI specifications.
    Provides common functionality for client generators.
    """

    method_template_map: dict[str, str]
    results: dict[str, int]
    spec: cicerone_openapi_spec.OpenAPISpec
    output_dir: str
    schemas_generator: typing.Any  # Type will be specific in subclasses
    http_generator: typing.Any  # Type will be specific in subclasses
    writer: typing.Any  # Must be set by subclass

    def __init__(
        self,
        spec: cicerone_openapi_spec.OpenAPISpec,
        output_dir: str,
        schemas_generator: typing.Any,
        http_generator: typing.Any,
        asyncio: bool,
    ) -> None:
        self.spec = spec
        self.output_dir = output_dir
        self.results = collections.defaultdict(int)
        self.schemas_generator = schemas_generator
        self.http_generator = http_generator
        self.asyncio = asyncio
        self.method_template_map = dict(
            get="get_method.jinja2",
            delete="get_method.jinja2",
            post="post_method.jinja2",
            put="post_method.jinja2",
            patch="post_method.jinja2",
        )

    def generate_paths(self) -> None:
        # Check if the spec has paths
        if not self.spec.paths or not self.spec.paths.items:
            console.log("No paths found in spec, skipping client generation...")
            return

        for path, path_item in self.spec.paths.items.items():
            # Convert path_item to operations dict using centralized compat layer
            operations_dict = cicerone_compat.path_item_to_operations_dict(path_item)
            self.write_path_to_client((path, operations_dict))
        console.log(f"Generated {self.results['get']} GET methods...")
        console.log(f"Generated {self.results['post']} POST methods...")
        console.log(f"Generated {self.results['put']} PUT methods...")
        console.log(f"Generated {self.results['patch']} PATCH methods...")
        console.log(f"Generated {self.results['delete']} DELETE methods...")

    def generate_parameters(self, parameters: list[dict], additional_parameters: list[dict]) -> ParametersResponse:
        param_keys = []
        query_args = {}
        path_args = {}
        headers_args = {}
        param_name_map = {}  # Maps sanitized name to original name
        all_parameters = parameters + additional_parameters
        for param in all_parameters:
            if param.get("$ref"):
                # Get the actual parameter it is referencing
                param = utils.get_param_from_ref(spec=self.spec, param=param)
            # Sanitize the parameter name to be a valid Python identifier
            original_name = param["name"]
            clean_key = utils.snake_case_prop(original_name)
            if clean_key in param_keys:
                continue
            # Store mapping from sanitized to original name
            param_name_map[clean_key] = original_name
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
            param_name_map=param_name_map,
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
            # Handle responses without content (e.g., 204 No Content)
            if "content" not in details or not details.get("content"):
                # For no-content responses, use None as the response type
                status_code_map[status_code] = "None"
                # Don't add None to response_classes list as it's not a schema class
                continue

            for _, content in details.get("content", {}).items():
                # Skip if no schema is defined (e.g., only examples)
                if "schema" not in content:
                    console.log(f"[yellow]Warning: Response {status_code} has no schema, using typing.Any")
                    class_name = utils.class_name_titled(func_name + status_code + "Response")
                    # Generate a minimal schema with Any type
                    self.schemas_generator.make_schema_class(
                        func_name + status_code + "Response",
                        schema={"type": "object", "properties": {"data": {"type": "object"}}},
                    )
                    status_code_map[status_code] = class_name
                    response_classes.append(class_name)
                    continue

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
                    # It is likely it isn't an object it is just a simple response.
                    class_name = utils.class_name_titled(func_name + status_code + "Response")
                    # We need to generate the class at this point because it does not exist
                    # Pass the schema directly - make_schema_class knows how to handle arrays
                    self.schemas_generator.make_schema_class(
                        func_name + status_code + "Response",
                        schema=content["schema"],
                    )
                status_code_map[status_code] = class_name
                response_classes.append(class_name)
        self.http_generator.add_status_codes_to_bundle(func_name=func_name, status_code_map=status_code_map)
        # Use set to deduplicate, then sorted for consistent ordering
        return sorted(set(response_classes))

    def get_input_class_names(self, inputs: dict, func_name: str) -> list[str]:
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
                    # Use function name + encoding to create unique class name
                    class_name = f"{func_name}_{encoding}"
                class_name = utils.class_name_titled(class_name)
                input_classes.append(class_name)
        # Return deduplicated list - order doesn't matter for this use case
        return list(set(input_classes))

    def generate_response_types(self, responses: dict, func_name: str) -> str:
        response_class_names = self.get_response_class_names(responses=responses, func_name=func_name)
        if len(response_class_names) > 1:
            return utils.union_for_py_ver([f"schemas.{r}" for r in response_class_names])
        elif len(response_class_names) == 0:
            return "None"
        else:
            return f"schemas.{response_class_names[0]}"

    def generate_input_types(self, request_body: dict, func_name: str) -> str:
        input_class_names = self.get_input_class_names(inputs={"": request_body}, func_name=func_name)
        for input_class in input_class_names:
            if input_class not in self.schemas_generator.schemas.keys():
                # It doesn't exist! Generate the schema for it
                self.schemas_generator.generate_input_class(schema=request_body, func_name=func_name)
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
        summary: typing.Optional[str],
    ) -> None:
        func_name = utils.get_func_name(operation, url)

        # Handle missing responses (OpenAPI spec violation, but handle gracefully)
        if "responses" not in operation:
            console.log(f"[yellow]Warning: Operation {func_name} has no responses defined, using default 200 response")
            responses = {"200": {"description": "Success"}}
        else:
            responses = operation["responses"]

        response_types = self.generate_response_types(responses=responses, func_name=func_name)
        function_arguments = self.generate_parameters(
            parameters=operation.get("parameters", []),
            additional_parameters=additional_parameters,
        )
        # Replace path parameters in URL with sanitized names
        api_url = utils.replace_path_parameters(url, function_arguments.param_name_map)
        if query_args := function_arguments.query_args:
            # Use original parameter names in URL, but sanitized names for Python variables
            api_url = api_url + utils.create_query_args_with_mapping(
                list(query_args.keys()), function_arguments.param_name_map
            )
        if method in ["post", "put", "patch"] and not operation.get("requestBody"):
            data_class_name = "None"
        elif method in ["post", "put", "patch"]:
            data_class_name = self.generate_input_types(operation.get("requestBody", {}), func_name=func_name)
        else:
            data_class_name = None
        self.results[method] += 1
        template = self.writer.templates.get_template(self.method_template_map[method])
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
            function_arguments=function_arguments,  # Pass the object, not the string
            response_types=response_types,
            data_class_name=data_class_name,
            header_class_name=header_class_name,
            api_url=api_url,
            method=method,
            summary=operation.get("summary", summary),
            description=operation.get("description"),
            deprecated=operation.get("deprecated", False),
        )
        self.writer.write_to_client(content=content, output_dir=self.output_dir)

    def write_path_to_client(self, path: tuple[str, dict]) -> None:
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
