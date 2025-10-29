"""
Wrapper for schemas generator that uses classbase writer.
"""
from openapi_core import Spec

from clientele.generators.classbase import writer
from clientele.generators.standard import utils
from clientele.generators.standard.generators.schemas import SchemasGenerator as StandardSchemasGenerator


class SchemasGenerator(StandardSchemasGenerator):
    """
    Schemas generator that uses the classbase writer instead of standard writer.
    Overrides methods that write to schemas to use our writer.
    """

    def __init__(self, spec: Spec, output_dir: str) -> None:
        # Initialize parent but we'll override writer calls
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir
        self.generated_response_class_names = []

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        """
        Generate a headers class that can be used by a function.
        Uses classbase writer.
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

    def make_schema_class(self, schema_key: str, schema: dict) -> None:
        """
        Make a schema class. Uses classbase writer.
        """
        schema_key = utils.class_name_titled(schema_key)
        if schema_key in self.schemas.keys():
            return

        enum = False
        properties: str = ""
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
        writer.write_to_schemas(content, output_dir=self.output_dir)

    def generate_input_class(self, schema: dict) -> None:
        """Generate input class. Uses classbase writer."""
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

    def write_helpers(self) -> None:
        """
        Write helper functions to schemas. Uses classbase writer.
        """
        template = writer.templates.get_template("schema_helpers.jinja2")
        content = template.render()
        writer.write_to_schemas(content, output_dir=self.output_dir)
