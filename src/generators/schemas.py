from typing import Optional

from openapi_core import Spec
from rich.console import Console

from src.settings import templates
from src.utils import (
    class_name_titled,
    clean_prop,
    get_schema_from_ref,
    get_type,
    schema_ref,
)
from src.writer import write_to_schemas

console = Console()


class SchemasGenerator:
    """
    Handles all the content generated in the schemas.py file.
    """

    spec: Spec
    schemas: dict[str, str]
    output_dir: str

    def __init__(self, spec: Spec, output_dir: str) -> None:
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir

    generated_response_class_names: list[str] = []

    def generate_enum_properties(self, properties: dict) -> str:
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

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        """
        Generate a headers class that can be used by a function.
        Returns the name of the class that has been created.
        Headers are special because they usually want to output keys that
        have - separators and python detests that, so we're using
        the alias trick to get around that
        """
        template = templates.get_template("schema_class.jinja2")
        class_name = f"{class_name_titled(func_name)}Headers"
        string_props = "\n".join(
            f'    {clean_prop(k)}: {v} = pydantic.Field(serialization_alias="{k}")'
            for k, v in properties.items()
        )
        content = template.render(
            class_name=class_name, properties=string_props, enum=False
        )
        write_to_schemas(
            content,
            output_dir=self.output_dir,
        )
        return f"typing.Optional[schemas.{class_name_titled(func_name)}Headers]"

    def generate_class_properties(
        self, properties: dict, required: Optional[list] = None
    ) -> str:
        """
        Generate a string list of the properties for this pydantic class.
        """
        content = ""
        for arg, arg_details in properties.items():
            arg_type = get_type(arg_details)
            is_optional = required and arg not in required
            content = (
                content
                + f"""    {clean_prop(arg)}: {is_optional and f"typing.Optional[{arg_type}]" or arg_type}\n"""
            )
        return content

    def generate_input_class(self, schema: dict) -> None:
        if content := schema.get("content"):
            for encoding, input_schema in content.items():
                class_name = ""
                if ref := input_schema["schema"].get("$ref", False):
                    class_name = class_name_titled(schema_ref(ref))
                elif title := input_schema["schema"].get("title", False):
                    class_name = class_name_titled(title)
                else:
                    # No idea, using the encoding?
                    class_name = class_name_titled(encoding)
                properties = self.generate_class_properties(
                    properties=input_schema["schema"].get("properties", {}),
                    required=input_schema["schema"].get("required", None),
                )
                template = templates.get_template("schema_class.jinja2")
                out_content = template.render(
                    class_name=class_name, properties=properties, enum=False
                )
            write_to_schemas(
                out_content,
                output_dir=self.output_dir,
            )

    def generate_schema_classes(self) -> None:
        """
        Generates the Pydantic response classes.
        """
        for schema_key, schema in self.spec["components"]["schemas"].items():
            schema_key = class_name_titled(schema_key)
            enum = False
            properties: str = ""
            if all_of := schema.get("allOf"):
                # This schema uses "all of" the properties from another model
                for other_ref in all_of:
                    other_schema_key = class_name_titled(schema_ref(other_ref["$ref"]))
                    if other_schema_key in self.schemas:
                        properties += self.schemas[other_schema_key]
                    else:
                        # We need to generate it now
                        schema_model = get_schema_from_ref(
                            spec=self.spec, ref=other_ref["$ref"]
                        )
                        properties += self.generate_class_properties(
                            properties=schema_model.get("properties", {}),
                            required=schema_model.get("required", None),
                        )
            elif schema.get("enum"):
                enum = True
                properties = self.generate_enum_properties(
                    {v: {"type": f'"{v}"'} for v in schema["enum"]}
                )
            else:
                properties = self.generate_class_properties(
                    properties=schema.get("properties", {}),
                    required=schema.get("required", None),
                )
            self.schemas[schema_key] = properties
            template = templates.get_template("schema_class.jinja2")
            content = template.render(
                class_name=schema_key, properties=properties, enum=enum
            )
            write_to_schemas(
                content,
                output_dir=self.output_dir,
            )

        console.log(f"Generated {len(self.schemas.items())} schemas...")
