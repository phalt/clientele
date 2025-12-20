"""Generator for OpenAPI 3.0 callback handlers."""

import typing

import openapi_core
from rich import console as rich_console

from clientele.generators.standard import utils, writer

console = rich_console.Console()


class CallbacksGenerator:
    """
    Handles all the content generated for OpenAPI callbacks.
    
    Callbacks represent webhook-style operations where the API calls back
    to the client at a URL the client provides. This generator creates:
    - Schemas for callback request/response bodies
    - Handler function signatures for callbacks the client needs to implement
    """

    spec: openapi_core.Spec
    callbacks: dict[str, dict]
    output_dir: str

    def __init__(self, spec: openapi_core.Spec, output_dir: str) -> None:
        self.spec = spec
        self.callbacks = {}
        self.output_dir = output_dir

    def extract_callbacks_from_spec(self) -> None:
        """
        Extract all callbacks from the OpenAPI spec.
        Callbacks are defined within operations in the paths section.
        """
        if "paths" not in self.spec:
            return

        for path_name, path_item in self.spec["paths"].items():
            for method in ["get", "post", "put", "patch", "delete"]:
                if method not in path_item:
                    continue
                    
                operation = path_item[method]
                if "callbacks" not in operation:
                    continue

                operation_id = operation.get("operationId", f"{method}_{path_name}")
                
                for callback_name, callback in operation["callbacks"].items():
                    # Each callback can have multiple expressions (URLs)
                    for expression, callback_path_item in callback.items():
                        for callback_method, callback_operation in callback_path_item.items():
                            # Store callback information
                            callback_key = f"{operation_id}_{callback_name}_{callback_method}"
                            self.callbacks[callback_key] = {
                                "operation_id": operation_id,
                                "callback_name": callback_name,
                                "expression": expression,
                                "method": callback_method,
                                "operation": callback_operation,
                                "path": path_name,
                            }

    def generate_callback_schemas(self, schemas_generator) -> None:
        """
        Generate Pydantic schemas for callback request and response bodies.
        
        Args:
            schemas_generator: The main schemas generator to add callback schemas to
        """
        if not self.callbacks:
            return

        console.log(f"Generating {len(self.callbacks)} callback schemas...")

        for callback_key, callback_info in self.callbacks.items():
            operation = callback_info["operation"]
            callback_name = callback_info["callback_name"]
            method = callback_info["method"]

            # Generate schema for request body if present
            if "requestBody" in operation:
                request_body = operation["requestBody"]
                if "content" in request_body:
                    for content_type, media_type in request_body["content"].items():
                        if "schema" in media_type:
                            schema = media_type["schema"]
                            # Generate inline schema class
                            class_name = utils.class_name_titled(
                                f"{callback_name}_{method}_callback_request"
                            )
                            
                            # Add to schemas generator
                            if "properties" in schema:
                                properties = schemas_generator.generate_class_properties(
                                    properties=schema.get("properties", {}),
                                    required=schema.get("required", None),
                                )
                                schemas_generator.schemas[class_name] = properties
                                template = writer.templates.get_template("schema_class.jinja2")
                                content = template.render(
                                    class_name=class_name,
                                    properties=properties,
                                    enum=False,
                                )
                                writer.write_to_schemas(content, output_dir=self.output_dir)

            # Generate schemas for responses if present
            if "responses" in operation:
                for status_code, response in operation["responses"].items():
                    if "content" in response:
                        for content_type, media_type in response["content"].items():
                            if "schema" in media_type:
                                schema = media_type["schema"]
                                class_name = utils.class_name_titled(
                                    f"{callback_name}_{method}_{status_code}_callback_response"
                                )
                                
                                if "properties" in schema:
                                    properties = schemas_generator.generate_class_properties(
                                        properties=schema.get("properties", {}),
                                        required=schema.get("required", None),
                                    )
                                    schemas_generator.schemas[class_name] = properties
                                    template = writer.templates.get_template("schema_class.jinja2")
                                    content = template.render(
                                        class_name=class_name,
                                        properties=properties,
                                        enum=False,
                                    )
                                    writer.write_to_schemas(content, output_dir=self.output_dir)

    def generate_callback_documentation(self) -> str:
        """
        Generate documentation and handler signatures for callbacks.
        
        Returns:
            String containing Python code with callback handler signatures and docs
        """
        if not self.callbacks:
            return ""

        lines = [
            '"""',
            "Callback Handlers",
            "==================",
            "",
            "This file contains signatures for callback handlers that your application",
            "needs to implement to receive webhook-style notifications from the API.",
            "",
            "Callbacks are defined in the OpenAPI spec and represent endpoints that",
            "the API will call on your server.",
            '"""',
            "",
            "from __future__ import annotations",
            "",
            "import typing",
            "",
            "from . import schemas",
            "",
            "",
        ]

        for callback_key, callback_info in self.callbacks.items():
            callback_name = callback_info["callback_name"]
            method = callback_info["method"].upper()
            expression = callback_info["expression"]
            operation = callback_info["operation"]
            description = operation.get("description", "")

            # Generate function signature
            func_name = utils.snake_case_prop(f"{callback_name}_handler")
            
            # Determine request body type
            request_type = "typing.Any"
            if "requestBody" in operation:
                request_body = operation["requestBody"]
                if "content" in request_body:
                    for content_type, media_type in request_body["content"].items():
                        if "schema" in media_type:
                            request_type = f"schemas.{utils.class_name_titled(f'{callback_name}_{method.lower()}_callback_request')}"
                            break

            # Determine response types and collect status codes
            response_types = []
            status_codes = []
            if "responses" in operation:
                for status_code, response in operation["responses"].items():
                    status_codes.append(status_code)
                    if "content" in response:
                        for content_type, media_type in response["content"].items():
                            if "schema" in media_type:
                                response_type = f"schemas.{utils.class_name_titled(f'{callback_name}_{method.lower()}_{status_code}_callback_response')}"
                                response_types.append(response_type)
                                break

            # Only use response types if we have content responses, otherwise None
            return_type = " | ".join(response_types) if response_types else "None"
            status_codes_str = ", ".join(status_codes) if status_codes else "any"

            lines.extend([
                f"def {func_name}(request: {request_type}) -> {return_type}:",
                f'    """',
                f"    Callback: {callback_name}",
                f"    Method: {method}",
                f"    URL Expression: {expression}",
                f"    Expected Response Status Codes: {status_codes_str}",
                "",
            ])

            if description:
                lines.append(f"    {description}")
                lines.append("")

            lines.extend([
                "    Your application needs to implement this handler to receive",
                "    callback notifications from the API at the specified URL.",
                "",
                "    Args:",
                f"        request: The callback request data",
                "",
                "    Returns:",
                f"        {return_type}",
                '    """',
                "    raise NotImplementedError(",
                f'        "Callback handler {func_name} must be implemented by your application"',
                "    )",
                "",
                "",
            ])

        return "\n".join(lines)

    def write_callbacks_file(self) -> None:
        """Write the callbacks.py file with handler signatures and documentation."""
        if not self.callbacks:
            console.log("No callbacks found in spec")
            return

        content = self.generate_callback_documentation()
        callbacks_file = f"{self.output_dir}/callbacks.py"
        
        with open(callbacks_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        console.log(f"Generated {len(self.callbacks)} callback handlers in callbacks.py")
