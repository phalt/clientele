import typing

from cicerone.spec import openapi_spec as cicerone_openapi_spec
from rich import console as rich_console

from clientele.generators import cicerone_compat
from clientele.generators.standard import utils, writer

console = rich_console.Console()


class SchemasGenerator:
    """
    Handles all the content generated in the schemas.py file.
    """

    spec: cicerone_openapi_spec.OpenAPISpec
    schemas: dict[str, str]
    output_dir: str

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec, output_dir: str) -> None:
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir

    generated_response_class_names: list[str] = []

    def generate_enum_properties(self, properties: dict) -> str:
        """
        Generate a string list of the properties for this enum.
        """
        # utils already imported
        lines = [
            f"    {utils.snake_case_prop(arg.upper())} = {utils.get_type(arg_details)}\n"
            for arg, arg_details in properties.items()
        ]
        return "".join(lines)

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        """
        Generate a headers class that can be used by a function.
        Returns the name of the class that has been created.
        Headers are special because they usually want to output keys that
        have - separators and python detests that, so we're using
        the alias trick to get around that
        """
        # utils already imported
        template = writer.templates.get_template("schema_class.jinja2")
        class_name = f"{utils.class_name_titled(func_name)}Headers"
        string_props = "\n".join(
            f'    {utils.snake_case_prop(k)}: {v} = pydantic.Field(serialization_alias="{k}")'
            for k, v in properties.items()
        )
        content = template.render(class_name=class_name, properties=string_props, enum=False)
        writer.write_to_schemas(
            content,
            output_dir=self.output_dir,
        )
        return f"typing.Optional[schemas.{utils.class_name_titled(func_name)}Headers]"

    def generate_class_properties(self, properties: dict, required: typing.Optional[list] = None) -> str:
        """
        Generate a string list of the properties for this pydantic class.
        """
        lines = []
        for arg, arg_details in properties.items():
            # Sanitize property names to ensure valid Python identifiers
            sanitized_arg = utils.snake_case_prop(arg)
            arg_type = utils.get_type(arg_details)
            is_optional = required and arg not in required
            # Only wrap in Optional if not already optional (e.g., from nullable)
            if is_optional and not arg_type.startswith("typing.Optional["):
                type_string = f"typing.Optional[{arg_type}] = None"
            elif arg_type.startswith("typing.Optional["):
                # Field is already Optional (e.g., from nullable), add default
                type_string = f"{arg_type} = None"
            else:
                type_string = arg_type
            lines.append(f"    {sanitized_arg}: {type_string}\n")
        return "".join(lines)

    def generate_input_class(self, schema: dict, func_name: str) -> None:
        if content := schema.get("content"):
            for encoding, input_schema in content.items():
                class_name = ""
                if ref := input_schema["schema"].get("$ref", False):
                    class_name = utils.class_name_titled(utils.schema_ref(ref))
                elif title := input_schema["schema"].get("title", False):
                    class_name = utils.class_name_titled(title)
                else:
                    # Use function name + encoding to create unique class name
                    class_name = utils.class_name_titled(f"{func_name}_{encoding}")
                properties = self.generate_class_properties(
                    properties=input_schema["schema"].get("properties", {}),
                    required=input_schema["schema"].get("required", None),
                )
                template = writer.templates.get_template("schema_class.jinja2")
                out_content = template.render(class_name=class_name, properties=properties, enum=False)
            writer.write_to_schemas(
                out_content,
                output_dir=self.output_dir,
            )

    def _create_union_type_alias(self, schema_key: str, schema_options: list[dict]) -> None:
        """
        Create a type alias for oneOf or anyOf schemas.

        Args:
            schema_key: Name of the schema
            schema_options: List of schema options from oneOf or anyOf
        """
        union_types = []
        for schema_option in schema_options:
            if ref := schema_option.get("$ref"):
                ref_name = utils.class_name_titled(utils.schema_ref(ref))
                union_types.append(f'"{ref_name}"')
            else:
                # Inline schema - convert to type
                union_types.append(utils.get_type(schema_option))
        template = writer.templates.get_template("schema_type_alias.jinja2")
        union_type = utils.union_for_py_ver(union_types)
        content = template.render(class_name=schema_key, union_type=union_type)
        writer.write_to_schemas(
            content,
            output_dir=self.output_dir,
        )
        self.schemas[schema_key] = ""  # Mark as processed

    def make_schema_class(self, schema_key: str, schema: dict) -> None:
        schema_key = utils.class_name_titled(schema_key)
        enum = False
        properties: str = ""

        # Handle oneOf - create a type alias
        if one_of := schema.get("oneOf"):
            self._create_union_type_alias(schema_key, one_of)
            return

        # Handle anyOf - create a type alias
        if any_of := schema.get("anyOf"):
            self._create_union_type_alias(schema_key, any_of)
            return

        # Handle array type - create a type alias for list types
        if schema.get("type") == "array":
            array_type = utils.get_type(schema)
            template = writer.templates.get_template("schema_type_alias.jinja2")
            content = template.render(class_name=schema_key, union_type=array_type)
            writer.write_to_schemas(
                content,
                output_dir=self.output_dir,
            )
            self.schemas[schema_key] = ""  # Mark as processed
            return

        if all_of := schema.get("allOf"):
            # This schema uses "all of" the properties inside it
            property_parts = []
            for other_ref in all_of:
                is_ref = other_ref.get("$ref", False)
                if is_ref:
                    other_schema_key = utils.class_name_titled(utils.schema_ref(is_ref))
                    if other_schema_key in self.schemas:
                        property_parts.append(self.schemas[other_schema_key])
                    else:
                        # It's a ref but we've just not made it yet
                        schema_model = utils.get_schema_from_ref(spec=self.spec, ref=is_ref)
                        property_parts.append(
                            self.generate_class_properties(
                                properties=schema_model.get("properties", {}),
                                required=schema_model.get("required", None),
                            )
                        )
                else:
                    # It's not a ref and we need to figure out what it is
                    if other_ref.get("type") == "object":
                        property_parts.append(
                            self.generate_class_properties(
                                properties=other_ref.get("properties", {}),
                                required=other_ref.get("required", None),
                            )
                        )
            properties = "".join(property_parts)
        elif schema.get("enum"):
            enum = True
            properties = self.generate_enum_properties({v: {"type": f'"{v}"'} for v in schema["enum"]})
        else:
            properties = self.generate_class_properties(
                properties=schema.get("properties", {}),
                required=schema.get("required", None),
            )
        self.schemas[schema_key] = properties
        template = writer.templates.get_template("schema_class.jinja2")
        content = template.render(class_name=schema_key, properties=properties, enum=enum)
        writer.write_to_schemas(
            content,
            output_dir=self.output_dir,
        )

    def write_helpers(self) -> None:
        template = writer.templates.get_template("schema_helpers.jinja2")
        content = template.render()
        writer.write_to_schemas(
            content,
            output_dir=self.output_dir,
        )

    def generate_schema_classes(self) -> None:
        """
        Generates all Pydantic schema classes.
        """
        # Check if the spec has components and schemas
        if not self.spec.components:
            console.log("No components found in spec, skipping schema generation...")
            return

        if not self.spec.components.schemas:
            console.log("No schemas found in components, skipping schema generation...")
            return

        for schema_key, schema in self.spec.components.schemas.items():
            # Convert cicerone Schema to dict-like structure
            schema_dict = cicerone_compat.schema_to_dict(schema)
            self.make_schema_class(schema_key=schema_key, schema=schema_dict)
        console.log(f"Generated {len(self.schemas.items())} schemas...")
