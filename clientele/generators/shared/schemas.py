import json
import typing

from cicerone.spec import openapi_spec as cicerone_openapi_spec
from rich import console as rich_console

from clientele.generators import cicerone_compat
from clientele.generators.shared import utils

console = rich_console.Console()


def build_union_type_string(
    schema_options: list[typing.Dict[str, typing.Any]],
    discriminator: typing.Optional[str] = None,
) -> str:
    """
    Build a union type string from a list of schema options (for oneOf or anyOf).

    Args:
        schema_options: List of schema option dictionaries from oneOf or anyOf
        discriminator: Optional discriminator property name for discriminated unions

    Returns:
        A union type string (e.g., "Cat | Dog" or "typing.Union[Cat, Dog]")
        When discriminator is provided, returns:
        "typing.Annotated[Cat | Dog, pydantic.Field(discriminator='type')]"
    """
    union_types = []
    for schema_option in schema_options:
        if ref := schema_option.get("$ref"):
            ref_name = utils.class_name_titled(utils.schema_ref(ref))
            # Use direct reference without quotes for type aliases
            union_types.append(ref_name)
        else:
            # Inline schema - convert to type and remove forward ref quotes
            type_str = utils.get_type(schema_option)
            type_str = utils.remove_forward_ref_quotes(type_str)
            union_types.append(type_str)

    union_str = utils.union_for_py_ver(union_types)

    # Wrap with Annotated + Field(discriminator=...) if discriminator is present
    if discriminator:
        return f'typing.Annotated[{union_str}, pydantic.Field(discriminator="{discriminator}")]'

    return union_str


class SchemasGenerator:
    """
    Handles all the content generated in the schemas.py file.
    Shared between api and any future generators.
    """

    spec: cicerone_openapi_spec.OpenAPISpec
    schemas: dict[str, str]
    output_dir: str
    writer: typing.Any

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec, output_dir: str, writer: typing.Any) -> None:
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir
        self.writer = writer

    def _enum_member_name(self, value: typing.Any) -> str:
        if value is None:
            return "NULL"
        if isinstance(value, str):
            return utils.snake_case_prop(value.upper())
        # Non-string members (ints, floats, bools) cannot be used as
        # identifiers directly, so synthesize a VALUE_<n> name.
        name = f"VALUE_{value}".replace("-", "MINUS_").replace(".", "_")
        return utils.snake_case_prop(name.upper())

    def _enum_base_class(self, values: list) -> str:
        if all(isinstance(v, str) for v in values):
            return "str, enum.Enum"
        # bool is a subclass of int but enum.IntEnum cannot hold it
        if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
            return "enum.IntEnum"
        return "enum.Enum"

    def generate_enum_properties(self, values: list) -> str:
        lines = []
        seen: dict[str, int] = {}
        for value in values:
            name = self._enum_member_name(value)
            count = seen.get(name, 0) + 1
            seen[name] = count
            if count > 1:
                name = f"{name}_{count}"
            py_value = json.dumps(value) if isinstance(value, str) else repr(value)
            lines.append(f"    {name} = {py_value}\n")
        return "".join(lines)

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        template = self.writer.templates.get_template("schema_class.jinja2")
        class_name = f"{utils.class_name_titled(func_name)}Headers"
        string_props = "\n".join(
            f'    {utils.snake_case_prop(k)}: {v} = pydantic.Field(serialization_alias="{k}")'
            for k, v in properties.items()
        )
        content = template.render(class_name=class_name, properties=string_props, enum=False)
        self.writer.write_to_schemas(content, output_dir=self.output_dir)
        return f"typing.Optional[schemas.{utils.class_name_titled(func_name)}Headers]"

    def generate_class_properties(self, properties: dict, required: typing.Optional[list] = None) -> str:
        lines = []
        has_aliases = False

        for arg, arg_details in properties.items():
            sanitized_arg = utils.snake_case_prop(arg)
            arg_type = utils.get_type(arg_details)
            is_optional = required and arg not in required
            has_default = "default" in arg_details

            needs_alias = sanitized_arg != arg
            if needs_alias:
                has_aliases = True

            if has_default:
                py_default = repr(arg_details["default"])
                if needs_alias:
                    type_string = f'{arg_type} = pydantic.Field(default={py_default}, alias="{arg}")'
                else:
                    type_string = f"{arg_type} = {py_default}"
            elif is_optional and not arg_type.startswith("typing.Optional["):
                if needs_alias:
                    type_string = f'typing.Optional[{arg_type}] = pydantic.Field(default=None, alias="{arg}")'
                else:
                    type_string = f"typing.Optional[{arg_type}] = None"
            elif arg_type.startswith("typing.Optional["):
                if needs_alias:
                    type_string = f'{arg_type} = pydantic.Field(default=None, alias="{arg}")'
                else:
                    type_string = f"{arg_type} = None"
            else:
                if needs_alias:
                    type_string = f'{arg_type} = pydantic.Field(alias="{arg}")'
                else:
                    type_string = arg_type
            lines.append(f"    {sanitized_arg}: {type_string}\n")

        if has_aliases:
            lines.append("\n    model_config = pydantic.ConfigDict(populate_by_name=True)\n")

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
                    class_name = utils.class_name_titled(f"{func_name}_{encoding}")
                properties = self.generate_class_properties(
                    properties=input_schema["schema"].get("properties", {}),
                    required=input_schema["schema"].get("required", None),
                )
                template = self.writer.templates.get_template("schema_class.jinja2")
                out_content = template.render(class_name=class_name, properties=properties, enum=False)
            self.writer.write_to_schemas(out_content, output_dir=self.output_dir)

    def _create_union_type_alias(
        self,
        schema_key: str,
        schema_options: list[dict],
        discriminator: typing.Optional[str] = None,
    ) -> None:
        union_type = build_union_type_string(schema_options, discriminator=discriminator)
        template = self.writer.templates.get_template("schema_type_alias.jinja2")
        content = template.render(class_name=schema_key, union_type=union_type)
        self.writer.write_to_schemas(content, output_dir=self.output_dir)
        self.schemas[schema_key] = ""

    def make_schema_class(self, schema_key: str, schema: dict) -> None:
        schema_key = utils.class_name_titled(schema_key)
        enum = False
        enum_base = "str, enum.Enum"
        properties: str = ""

        if one_of := schema.get("oneOf"):
            discriminator = None
            if disc := schema.get("discriminator"):
                discriminator = disc.get("propertyName")
            self._create_union_type_alias(schema_key, one_of, discriminator=discriminator)
            return

        if any_of := schema.get("anyOf"):
            self._create_union_type_alias(schema_key, any_of)
            return

        if schema.get("type") == "array":
            # Emit a pydantic.RootModel subclass rather than a plain type alias.
            # list[...] is a GenericAlias, not a type, so pydantic rejects it
            # when it appears in response_map: dict[int, type[Any]].  A RootModel
            # subclass is a proper class and satisfies that constraint.
            items_schema = schema.get("items") or {}
            item_type = utils.get_type(items_schema) if items_schema else "typing.Any"
            item_type = utils.remove_forward_ref_quotes(item_type)
            template = self.writer.templates.get_template("schema_root_model.jinja2")
            content = template.render(class_name=schema_key, inner_type=item_type, base_class="ListResponse")
            self.writer.write_to_schemas(content, output_dir=self.output_dir)
            self.schemas[schema_key] = ""
            return

        additional_properties = schema.get("additionalProperties")
        if (
            schema.get("type") == "object"
            and isinstance(additional_properties, dict)
            and additional_properties
            and not schema.get("properties")
        ):
            # A pure map schema (additionalProperties, no properties) gets the
            # same root-model treatment as arrays so it is a real type that
            # validates its values.
            value_type = utils.remove_forward_ref_quotes(utils.get_type(additional_properties))
            template = self.writer.templates.get_template("schema_root_model.jinja2")
            content = template.render(class_name=schema_key, inner_type=value_type, base_class="DictResponse")
            self.writer.write_to_schemas(content, output_dir=self.output_dir)
            self.schemas[schema_key] = ""
            return

        if all_of := schema.get("allOf"):
            property_parts = []
            for other_ref in all_of:
                is_ref = other_ref.get("$ref", False)
                if is_ref:
                    other_schema_key = utils.class_name_titled(utils.schema_ref(is_ref))
                    if other_schema_key in self.schemas:
                        property_parts.append(self.schemas[other_schema_key])
                    else:
                        schema_model = utils.get_schema_from_ref(spec=self.spec, ref=is_ref)
                        property_parts.append(
                            self.generate_class_properties(
                                properties=schema_model.get("properties", {}),
                                required=schema_model.get("required", None),
                            )
                        )
                else:
                    if other_ref.get("type") == "object":
                        property_parts.append(
                            self.generate_class_properties(
                                properties=other_ref.get("properties", {}),
                                required=other_ref.get("required", None),
                            )
                        )
            properties = "".join(property_parts)
        elif enum_values := schema.get("enum"):
            enum = True
            enum_base = self._enum_base_class(enum_values)
            properties = self.generate_enum_properties(enum_values)
        else:
            properties = self.generate_class_properties(
                properties=schema.get("properties", {}),
                required=schema.get("required", None),
            )
        self.schemas[schema_key] = properties
        template = self.writer.templates.get_template("schema_class.jinja2")
        content = template.render(class_name=schema_key, properties=properties, enum=enum, enum_base=enum_base)
        self.writer.write_to_schemas(content, output_dir=self.output_dir)

    def write_helpers(self) -> None:
        template = self.writer.templates.get_template("schema_helpers.jinja2")
        content = template.render()
        self.writer.write_to_schemas(content, output_dir=self.output_dir)

    def generate_schema_classes(self) -> None:
        if not self.spec.components:
            console.log("No components found in spec, skipping schema generation...")
            return

        if not self.spec.components.schemas:
            console.log("No schemas found in components, skipping schema generation...")
            return

        for schema_key, schema in self.spec.components.schemas.items():
            schema_dict = cicerone_compat.schema_to_dict(schema)
            self.make_schema_class(schema_key=schema_key, schema=schema_dict)
        console.log(f"Generated {len(self.schemas.items())} schemas...")
