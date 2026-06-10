"""
Pre-flight validation of OpenAPI specs for clientele compatibility.

The generator assumes a well-formed spec: unresolvable $refs either crash
generation or silently produce broken output, and unsupported constructs
(cookie parameters, multipart bodies) are silently dropped. SpecValidator
walks a parsed spec and reports these up front:

  - errors:   constructs that break generation or produce broken code
  - warnings: constructs that degrade to less useful code

Used by the `clientele validate` CLI command.
"""

import dataclasses

from cicerone.spec import openapi_spec as cicerone_openapi_spec

from clientele.generators import cicerone_compat
from clientele.generators.shared import security

SCHEMA_REF_PREFIX = "#/components/schemas/"
PARAMETER_REF_PREFIX = "#/components/parameters/"

SUPPORTED_PARAMETER_LOCATIONS = ("query", "path", "header")


@dataclasses.dataclass
class Finding:
    severity: str  # "error" or "warning"
    location: str
    message: str


class SpecValidator:
    """Walks an OpenAPI spec and collects compatibility findings."""

    def __init__(self, spec: cicerone_openapi_spec.OpenAPISpec) -> None:
        self.spec = spec
        self.findings: list[Finding] = []
        self.schema_names: set[str] = set()
        self.parameter_names: set[str] = set()
        if spec.components:
            if spec.components.schemas:
                self.schema_names = set(spec.components.schemas)
            if getattr(spec.components, "parameters", None):
                self.parameter_names = set(spec.components.parameters)

    def validate(self) -> list[Finding]:
        self.findings = []
        self._check_security_schemes()
        self._check_component_schemas()
        self._check_paths()
        return self.findings

    def _check_security_schemes(self) -> None:
        auth = security.classify_security_schemes(self.spec)
        if not auth:
            return
        for scheme in auth["unsupported"]:
            self._warning(
                f"security scheme '{scheme['scheme_name']}' ({scheme['description']}) cannot be "
                "generated automatically; configure authentication manually in config.py",
                f"components.securitySchemes.{scheme['scheme_name']}",
            )

    def _error(self, message: str, location: str) -> None:
        self.findings.append(Finding(severity="error", location=location, message=message))

    def _warning(self, message: str, location: str) -> None:
        self.findings.append(Finding(severity="warning", location=location, message=message))

    def _check_ref(self, ref: str, location: str) -> None:
        if ref.startswith(SCHEMA_REF_PREFIX):
            name = ref[len(SCHEMA_REF_PREFIX) :]
            if name not in self.schema_names:
                self._error(f"$ref references missing schema '{name}'", location)
        elif ref.startswith(PARAMETER_REF_PREFIX):
            name = ref[len(PARAMETER_REF_PREFIX) :]
            if name not in self.parameter_names:
                self._error(f"$ref references missing parameter '{name}'", location)
        else:
            self._warning(
                f"$ref '{ref}' is not a component reference and will degrade to typing.Any",
                location,
            )

    def _walk_schema(self, schema, location: str) -> None:
        if not isinstance(schema, dict):
            return
        if ref := schema.get("$ref"):
            self._check_ref(ref, location)
            return
        for key in ("oneOf", "anyOf", "allOf"):
            for index, sub_schema in enumerate(schema.get(key) or []):
                self._walk_schema(sub_schema, f"{location}.{key}[{index}]")
        for prop_name, prop_schema in (schema.get("properties") or {}).items():
            self._walk_schema(prop_schema, f"{location}.{prop_name}")
        if items := schema.get("items"):
            self._walk_schema(items, f"{location}.items")
        additional_properties = schema.get("additionalProperties")
        if isinstance(additional_properties, dict):
            self._walk_schema(additional_properties, f"{location}.additionalProperties")

    def _check_component_schemas(self) -> None:
        if not (self.spec.components and self.spec.components.schemas):
            return
        for name, schema in self.spec.components.schemas.items():
            schema_dict = cicerone_compat.schema_to_dict(schema)
            self._walk_schema(schema_dict, f"components.schemas.{name}")

    def _check_paths(self) -> None:
        if not self.spec.paths or not self.spec.paths.items:
            return
        for path, path_item in self.spec.paths.items.items():
            operations = cicerone_compat.path_item_to_operations_dict(path_item)
            shared_parameters = operations.get("parameters", [])
            for method, operation in operations.items():
                if method == "parameters":
                    continue
                self._check_operation(operation, shared_parameters, f"{method.upper()} {path}")

    def _check_parameter(self, param: dict, location: str) -> None:
        in_ = param.get("in")
        name = param.get("name", "<unnamed>")
        if in_ == "cookie":
            self._warning(f"cookie parameter '{name}' is not supported and will be skipped", location)
        elif in_ not in SUPPORTED_PARAMETER_LOCATIONS:
            self._warning(f"parameter '{name}' has unsupported location '{in_}' and will be skipped", location)
        if schema := param.get("schema"):
            self._walk_schema(schema, f"{location} parameter '{name}'")

    def _check_operation(self, operation: dict, shared_parameters: list, location: str) -> None:
        for param in list(operation.get("parameters", [])) + list(shared_parameters):
            if not isinstance(param, dict):
                param = cicerone_compat.parameter_to_dict(param)
            if ref := param.get("$ref"):
                self._check_ref(ref, location)
                if not ref.startswith(PARAMETER_REF_PREFIX):
                    continue
                name = ref[len(PARAMETER_REF_PREFIX) :]
                if name not in self.parameter_names:
                    continue
                param = cicerone_compat.parameter_to_dict(self.spec.components.parameters[name])
            self._check_parameter(param, location)

        if request_body := operation.get("requestBody"):
            for content_type, content in (request_body.get("content") or {}).items():
                if content_type == "multipart/form-data":
                    self._warning(
                        "multipart/form-data request bodies are generated as plain models; "
                        "file upload fields are not supported",
                        location,
                    )
                if isinstance(content, dict) and "schema" in content:
                    self._walk_schema(content["schema"], f"{location} requestBody ({content_type})")

        if "responses" not in operation:
            self._warning(
                "operation has no responses defined; a default 200 response will be assumed",
                location,
            )
            return
        for status_code, response in operation["responses"].items():
            content = response.get("content") if isinstance(response, dict) else None
            if not content:
                # No-content responses (e.g. 204) are fully supported
                continue
            for content_type, media in content.items():
                if not isinstance(media, dict) or "schema" not in media:
                    self._warning(
                        f"response {status_code} ({content_type}) has no schema; typing.Any will be used",
                        location,
                    )
                    continue
                self._walk_schema(media["schema"], f"{location} response {status_code} ({content_type})")
