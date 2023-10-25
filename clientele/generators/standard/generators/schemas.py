from typing import Optional

from openapi_core import Spec
from rich.console import Console

from clientele.generators.standard import utils, writer

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
            content = content + f"""    {utils.snake_case_prop(arg.upper())} = {utils.get_type(arg_details)}\n"""
        return content

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        """
        Generate a headers class that can be used by a function.
        Returns the name of the class that has been created.
        Headers are special because they usually want to output keys that
        have - separators and python detests that, so we're using
        the alias trick to get around that
        """
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

    def generate_class_properties(self, properties: dict, required: Optional[list] = None) -> str:
        """
        Generate a string list of the properties for this pydantic class.
        """
        content = ""
        for arg, arg_details in properties.items():
            arg_type = utils.get_type(arg_details)
            is_optional = required and arg not in required
            type_string = is_optional and f"typing.Optional[{arg_type}]" or arg_type
            content = content + f"""    {arg}: {type_string}\n"""
        return content

    def generate_input_class(self, schema: dict) -> None:
        if content := schema.get("content"):
            for encoding, input_schema in content.items():
                class_name = ""
                if ref := input_schema["schema"].get("$ref", False):
                    class_name = utils.class_name_titled(utils.schema_ref(ref))
                elif title := input_schema["schema"].get("title", False):
                    class_name = utils.class_name_titled(title)
                else:
                    # No idea, using the encoding?
                    class_name = utils.class_name_titled(encoding)
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

    def make_schema_class(self, schema_key: str, schema: dict) -> None:
        schema_key = utils.class_name_titled(schema_key)
        enum = False
        properties: str = ""
        if all_of := schema.get("allOf"):
            # This schema uses "all of" the properties inside it
            for other_ref in all_of:
                is_ref = other_ref.get("$ref", False)
                if is_ref:
                    other_schema_key = utils.class_name_titled(utils.schema_ref(is_ref))
                    if other_schema_key in self.schemas:
                        properties += self.schemas[other_schema_key]
                    else:
                        # It's a ref but we've just not made it yet
                        schema_model = utils.get_schema_from_ref(spec=self.spec, ref=is_ref)
                        properties += self.generate_class_properties(
                            properties=schema_model.get("properties", {}),
                            required=schema_model.get("required", None),
                        )
                else:
                    # It's not a ref and we need to figure out what it is
                    if other_ref.get("type") == "object":
                        properties += self.generate_class_properties(
                            properties=other_ref.get("properties", {}),
                            required=other_ref.get("required", None),
                        )
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
        for schema_key, schema in self.spec["components"]["schemas"].items():
            self.make_schema_class(schema_key=schema_key, schema=schema)
        console.log(f"Generated {len(self.schemas.items())} schemas...")
