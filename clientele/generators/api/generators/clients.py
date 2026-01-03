import typing

from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators import base_clients
from clientele.generators.api import writer
from clientele.generators.api.generators import schemas


class FrameworkHTTPPlaceholder:
    """
    Placeholder for http_generator to store status codes.
    Framework generator doesn't generate http.py but needs to track status codes
    for response_map generation.
    """

    def __init__(self) -> None:
        self.function_and_status_codes_bundle: dict[str, dict[str, str]] = {}

    def add_status_codes_to_bundle(self, func_name: str, status_code_map: dict[str, str]) -> None:
        """Store status codes for generating response_map."""
        self.function_and_status_codes_bundle[func_name] = status_code_map


class ClientsGenerator(base_clients.BaseClientsGenerator):
    """
    Handles all the content generated in the client.py file for the api generator.
    This generates decorator-based client functions instead of traditional functions.
    """

    schemas_generator: schemas.SchemasGenerator
    http_placeholder: FrameworkHTTPPlaceholder

    def __init__(
        self,
        spec: cicerone_openapi_spec.OpenAPISpec,
        output_dir: str,
        schemas_generator: schemas.SchemasGenerator,
        asyncio: bool,
    ) -> None:
        # Create placeholder to track status codes
        self.http_placeholder = FrameworkHTTPPlaceholder()
        # Pass placeholder as http_generator to base class
        super().__init__(spec, output_dir, schemas_generator, self.http_placeholder, asyncio)
        self.writer = writer
        # Override template map for clientele-specific templates
        self.method_template_map = dict(
            get="api_get_method.jinja2",
            delete="api_get_method.jinja2",
            post="api_post_method.jinja2",
            put="api_post_method.jinja2",
            patch="api_post_method.jinja2",
        )

    def get_response_map(self, func_name: str) -> typing.Optional[str]:
        """
        Generate response_map for decorator if there are multiple response types.
        Returns a string representation of the response_map dict or None.
        """
        status_codes = self.http_placeholder.function_and_status_codes_bundle.get(func_name, {})

        # If there's only one response code, we don't need response_map
        if len(status_codes) <= 1:
            return None

        # Filter out None responses (no content responses)
        valid_responses = {code: schema for code, schema in status_codes.items() if schema != "None"}

        if len(valid_responses) <= 1:
            return None

        # Build response_map dict with schemas. prefix
        response_map_parts = []
        for status_code, schema_name in sorted(valid_responses.items()):
            # Add schemas. prefix to match the response types
            response_map_parts.append(f"{status_code}: schemas.{schema_name}")

        return "{" + ", ".join(response_map_parts) + "}"

    def generate_function(
        self,
        operation: dict,
        method: str,
        url: str,
        additional_parameters: list[dict],
        summary: typing.Optional[str],
    ) -> None:
        """Override to add response_map to template context and fix URL handling for clientele api."""
        from rich import console as rich_console

        from clientele.generators.standard import utils

        console = rich_console.Console()

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
        # Replace path parameters in URL with sanitized names but DON'T add query args
        # In the clientele api, query args are passed as function parameters, not in the URL
        api_url = utils.replace_path_parameters(url, function_arguments.param_name_map)

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

        # Get response_map for clientele api decorator
        response_map = self.get_response_map(func_name)

        content = template.render(
            asyncio=self.asyncio,
            func_name=func_name,
            function_arguments=function_arguments,
            response_types=response_types,
            data_class_name=data_class_name,
            header_class_name=header_class_name,
            api_url=api_url,
            method=method,
            summary=operation.get("summary", summary),
            description=operation.get("description"),
            deprecated=operation.get("deprecated", False),
            response_map=response_map,
        )
        self.writer.write_to_client(content=content, output_dir=self.output_dir)
