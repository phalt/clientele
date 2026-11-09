import heapq
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


def _eager_refs(schema: dict) -> set[str]:
    """
    Class names a `oneOf`/`anyOf` alias or `type: array` RootModel needs defined before it.

    These are evaluated at import time, so every `$ref` that ends up in the generated
    expression counts: the members, and anything nested in inline members or `items`
    (mirrors what `utils.get_type` renders). Other components have none: plain classes
    use forward references and `model_rebuild()`, and `allOf` inlines properties.
    """
    if not (schema.get("oneOf") or schema.get("anyOf") or schema.get("type") == "array"):
        return set()

    refs: set[str] = set()

    def walk(node: typing.Any) -> None:
        if not isinstance(node, dict):
            return
        if ref := node.get("$ref"):
            refs.add(utils.class_name_titled(utils.schema_ref(ref)))
        for member in (node.get("oneOf") or []) + (node.get("anyOf") or []):
            walk(member)
        walk(node.get("items"))

    walk(schema)
    return refs


def order_by_eager_refs(schemas: dict[str, dict]) -> list[str]:
    """
    Order component keys so each alias / array model comes after the components it references.

    Stable: keeps spec order, except that a component moves just after its last eager
    dependency. Components with no eager dependencies keep their relative order, so specs
    that already imported generate the same file. A cycle among eager definitions can't be
    expressed as module-level aliases; it falls back to spec order with a warning.
    """
    keys = list(schemas)
    index_by_name: dict[str, list[int]] = {}
    for i, key in enumerate(keys):
        index_by_name.setdefault(utils.class_name_titled(key), []).append(i)

    pending: list[set[int]] = []
    dependents: list[list[int]] = [[] for _ in keys]
    for i, key in enumerate(keys):
        deps = {j for name in _eager_refs(schemas[key]) for j in index_by_name.get(name, [])}
        pending.append(deps)
        for j in deps:
            dependents[j].append(i)

    ready = [i for i, deps in enumerate(pending) if not deps]
    heapq.heapify(ready)
    emitted = [False] * len(keys)
    order: list[str] = []
    while len(order) < len(keys):
        if ready:
            i = heapq.heappop(ready)
        else:
            i = min(j for j, done in enumerate(emitted) if not done)
            cycle = sorted(keys[j] for j, done in enumerate(emitted) if not done and pending[j])
            console.log(
                f"[yellow]Warning: reference cycle among schemas {', '.join(cycle)}; "
                f"emitting {keys[i]} in spec order, schemas.py may not import"
            )
        if emitted[i]:
            continue
        emitted[i] = True
        order.append(keys[i])
        for d in dependents[i]:
            pending[d].discard(i)
            if not pending[d] and not emitted[d]:
                heapq.heappush(ready, d)
    return order


def _admits_null(schema: dict) -> bool:
    """True if the schema itself allows null: `type: "null"` or a null member of `anyOf`/`oneOf`."""
    if schema.get("type") == "null":
        return True
    members = schema.get("anyOf") or schema.get("oneOf") or []
    return any(member.get("type") == "null" for member in members)


class SchemasGenerator:
    """
    Handles all the content generated in the schemas.py file.
    Shared between api and any future generators.
    """

    spec: cicerone_openapi_spec.OpenAPISpec
    schemas: dict[str, str]
    output_dir: str
    writer: typing.Any
    base_class: typing.Optional[str]

    def __init__(
        self,
        spec: cicerone_openapi_spec.OpenAPISpec,
        output_dir: str,
        writer: typing.Any,
        base_class: typing.Optional[str] = None,
    ) -> None:
        self.spec = spec
        self.schemas = {}
        self.output_dir = output_dir
        self.writer = writer
        # Dotted path (`my_pkg.models.Base`) of a user-supplied base class for generated models.
        # schemas_py.jinja2 imports it as `_ClienteleBase` so it can't clash with a component name.
        self.base_class = base_class

    @property
    def model_base(self) -> str:
        """The base class generated models subclass."""
        return "_ClienteleBase" if self.base_class else "pydantic.BaseModel"

    def generate_enum_properties(self, properties: dict) -> str:
        lines = []
        taken: set[str] = set()
        for arg, arg_details in properties.items():
            base = utils.snake_case_prop(arg.upper())
            # Values that differ only by dropped characters (e.g. "AAA" and "AA|A") get the
            # same base name, so add a numeric suffix to keep every member unique.
            name, suffix = base, 2
            while name in taken:
                name, suffix = f"{base}_{suffix}", suffix + 1
            taken.add(name)
            lines.append(f"    {name} = {utils.get_type(arg_details)}\n")
        return "".join(lines)

    def generate_headers_class(self, properties: dict, func_name: str) -> str:
        template = self.writer.templates.get_template("schema_class.jinja2")
        class_name = f"{utils.class_name_titled(func_name)}Headers"
        string_props = "\n".join(
            f'    {utils.snake_case_prop(k)}: {v} = pydantic.Field(serialization_alias="{k}")'
            for k, v in properties.items()
        )
        content = template.render(class_name=class_name, properties=string_props, enum=False, base=self.model_base)
        self.writer.write_to_schemas(content, output_dir=self.output_dir)
        return f"typing.Optional[schemas.{utils.class_name_titled(func_name)}Headers]"

    def generate_class_properties(self, properties: dict, required: typing.Optional[list] = None) -> str:
        lines = []
        has_aliases = False

        for arg, arg_details in properties.items():
            sanitized_arg = utils.snake_case_prop(arg)
            arg_type = utils.get_type(arg_details)
            # Per OpenAPI, a property is required only if it is listed in `required`.
            # A missing or empty `required` array means every property is optional.
            is_optional = arg not in (required or [])
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
                # Don't wrap a type that already admits None (e.g. `int | None`) in Optional again
                optional_type = arg_type if _admits_null(arg_details) else f"typing.Optional[{arg_type}]"
                if needs_alias:
                    type_string = f'{optional_type} = pydantic.Field(default=None, alias="{arg}")'
                else:
                    type_string = f"{optional_type} = None"
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
            lines.append("\n    model_config = pydantic.ConfigDict(populate_by_name=True, serialize_by_alias=True)\n")

        return "".join(lines)

    def generate_input_class(self, schema: dict, func_name: str, input_class: str | None = None) -> None:
        if content := schema.get("content"):
            for encoding, input_schema in content.items():
                class_name = ""
                if ref := input_schema["schema"].get("$ref", False):
                    class_name = utils.class_name_titled(utils.schema_ref(ref))
                elif title := input_schema["schema"].get("title", False):
                    class_name = utils.class_name_titled(title)
                else:
                    class_name = utils.class_name_titled(f"{func_name}_{encoding}")

                if input_class is not None and class_name != input_class:
                    continue

                properties = self.generate_class_properties(
                    properties=input_schema["schema"].get("properties", {}),
                    required=input_schema["schema"].get("required", None),
                )
                template = self.writer.templates.get_template("schema_class.jinja2")
                out_content = template.render(
                    class_name=class_name, properties=properties, enum=False, base=self.model_base
                )
                self.writer.write_to_schemas(out_content, output_dir=self.output_dir)
                self.schemas[class_name] = properties

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
            content = template.render(class_name=schema_key, inner_type=item_type)
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
        elif schema.get("enum"):
            enum = True
            properties = self.generate_enum_properties({v: {"type": f'"{v}"'} for v in schema["enum"]})
        else:
            properties = self.generate_class_properties(
                properties=schema.get("properties", {}),
                required=schema.get("required", None),
            )
        self.schemas[schema_key] = properties
        template = self.writer.templates.get_template("schema_class.jinja2")
        content = template.render(class_name=schema_key, properties=properties, enum=enum, base=self.model_base)
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

        schema_dicts = {
            schema_key: cicerone_compat.schema_to_dict(schema)
            for schema_key, schema in self.spec.components.schemas.items()
        }
        # Aliases and array models are evaluated at import time, so define what they reference first
        for schema_key in order_by_eager_refs(schema_dicts):
            self.make_schema_class(schema_key=schema_key, schema=schema_dicts[schema_key])
        console.log(f"Generated {len(self.schemas.items())} schemas...")
