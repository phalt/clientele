from typing import Dict, List

from openapi_core import Spec
from rich.console import Console

from src.utils import class_name_titled, clean_prop, get_type
from src.writer import write_to_schemas

console = Console()


class SchemasGenerator:
    """
    Handles all the content generated in the schemas.py file.
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
                    class_name = class_name_titled(title)
                else:
                    # No idea, using the encoding?
                    class_name = class_name_titled(encoding)
                properties = self.generate_class_properties(
                    input_schema["schema"].get("properties", {})
                )
                content = f"""
class {class_name}(BaseModel):
{properties if properties else "    pass"}
    """
            write_to_schemas(
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
                properties = self.generate_class_properties(
                    schema.get("properties", {})
                )
            self.schemas[schema_key] = properties
            content = f"""
class {schema_key}({"Enum" if enum else "BaseModel"}):
{properties if properties else "    pass"}
    """
            write_to_schemas(
                content,
                output_dir=self.output_dir,
            )

        console.log(f"Generated {len(self.schemas.items())} schemas...")
