"""Client introspection for dynamic discovery of operations."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import typing
from dataclasses import dataclass
from pathlib import Path


@dataclass
class OperationInfo:
    """Information about a single API operation."""

    name: str
    parameters: dict[str, dict[str, typing.Any]]  # {param_name: {type, required, default}}
    return_type: typing.Any
    docstring: str | None
    http_method: str
    function: typing.Callable


class ClientIntrospector:
    """Analyzes generated clientele clients to discover operations."""

    def __init__(self, client_path: Path):
        """Initialize the introspector.

        Args:
            client_path: Path to the generated client directory
        """
        self.client_path = Path(client_path)
        self.client_module = None
        self.schemas_module = None
        self.operations: dict[str, OperationInfo] = {}
        self.is_class_based = False
        self.client_instance = None

    def load_client(self) -> None:
        """Dynamically import the client and schemas modules."""
        client_file = self.client_path / "client.py"
        schemas_file = self.client_path / "schemas.py"
        http_file = self.client_path / "http.py"
        config_file = self.client_path / "config.py"
        init_file = self.client_path / "__init__.py"

        if not client_file.exists():
            raise FileNotFoundError(f"Client file not found: {client_file}")

        # Ensure __init__.py exists
        if not init_file.exists():
            init_file.write_text("")

        # Add the parent directory to sys.path for proper imports
        parent_path = str(self.client_path.parent.absolute())
        if parent_path not in sys.path:
            sys.path.insert(0, parent_path)

        # Generate a unique package name based on the client path
        package_name = self.client_path.name

        # Create package module
        spec = importlib.util.spec_from_file_location(package_name, init_file)
        if spec is None:
            raise ImportError(f"Could not create spec for package {package_name}")
        package_module = importlib.util.module_from_spec(spec)
        package_module.__path__ = [str(self.client_path)]
        sys.modules[package_name] = package_module

        # Import config module if it exists
        if config_file.exists():
            spec = importlib.util.spec_from_file_location(
                f"{package_name}.config", config_file, submodule_search_locations=[str(self.client_path)]
            )
            if spec and spec.loader:
                config_module = importlib.util.module_from_spec(spec)
                config_module.__package__ = package_name
                sys.modules[f"{package_name}.config"] = config_module
                spec.loader.exec_module(config_module)

        # Import schemas module if it exists
        if schemas_file.exists():
            spec = importlib.util.spec_from_file_location(
                f"{package_name}.schemas", schemas_file, submodule_search_locations=[str(self.client_path)]
            )
            if spec and spec.loader:
                self.schemas_module = importlib.util.module_from_spec(spec)
                self.schemas_module.__package__ = package_name
                sys.modules[f"{package_name}.schemas"] = self.schemas_module
                spec.loader.exec_module(self.schemas_module)

        # Import http module if it exists
        if http_file.exists():
            spec = importlib.util.spec_from_file_location(
                f"{package_name}.http", http_file, submodule_search_locations=[str(self.client_path)]
            )
            if spec and spec.loader:
                http_module = importlib.util.module_from_spec(spec)
                http_module.__package__ = package_name
                sys.modules[f"{package_name}.http"] = http_module
                spec.loader.exec_module(http_module)

        # Import client module (this must be last as it depends on others)
        spec = importlib.util.spec_from_file_location(
            f"{package_name}.client", client_file, submodule_search_locations=[str(self.client_path)]
        )
        if spec and spec.loader:
            self.client_module = importlib.util.module_from_spec(spec)
            self.client_module.__package__ = package_name
            sys.modules[f"{package_name}.client"] = self.client_module
            spec.loader.exec_module(self.client_module)

    def discover_operations(self) -> dict[str, OperationInfo]:
        """Discover all operations in the client.

        Returns:
            Dictionary mapping operation names to OperationInfo objects
        """
        if not self.client_module:
            raise RuntimeError("Client module not loaded. Call load_client() first.")

        # Check if this is a class-based client
        if hasattr(self.client_module, "Client"):
            self.is_class_based = True
            self._discover_class_operations()
        else:
            self._discover_function_operations()

        return self.operations

    def _discover_function_operations(self) -> None:
        """Discover operations in a function-based client."""
        for name, obj in inspect.getmembers(self.client_module, inspect.isfunction):
            # Skip private functions and imports
            if name.startswith("_"):
                continue

            # Analyze the function
            operation_info = self._analyze_operation(obj, name)
            if operation_info:
                self.operations[name] = operation_info

    def _discover_class_operations(self) -> None:
        """Discover operations in a class-based client."""
        client_class = getattr(self.client_module, "Client")

        # Create an instance (using default config)
        self.client_instance = client_class()

        for name, obj in inspect.getmembers(client_class, inspect.isfunction):
            # Skip private methods, __init__, and other special methods
            if name.startswith("_"):
                continue

            # Analyze the method
            operation_info = self._analyze_operation(obj, name, is_method=True)
            if operation_info:
                self.operations[name] = operation_info

    def _analyze_operation(self, func: typing.Callable, name: str, is_method: bool = False) -> OperationInfo | None:
        """Analyze a function/method to extract operation information.

        Args:
            func: The function or method to analyze
            name: The name of the operation
            is_method: Whether this is a class method (vs. function)

        Returns:
            OperationInfo object or None if analysis fails
        """
        try:
            sig = inspect.signature(func)
            parameters: dict[str, dict[str, typing.Any]] = {}

            # Skip 'self' parameter for methods and clientele-injected parameters
            params_to_skip = {"self"} if is_method else set()
            # Clientele-injected parameters that should not be exposed to users
            params_to_skip.update({"result", "response"})

            for param_name, param in sig.parameters.items():
                if param_name in params_to_skip:
                    continue

                # Extract type information
                param_type = param.annotation if param.annotation != inspect.Parameter.empty else typing.Any

                # Determine if required
                has_default = param.default != inspect.Parameter.empty
                required = not has_default

                parameters[param_name] = {
                    "type": param_type,
                    "required": required,
                    "default": param.default if has_default else None,
                }

            # Get return type
            return_type = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else None

            # Get docstring
            docstring = inspect.getdoc(func)

            # Try to determine HTTP method from function decorator, name, or docstring
            http_method = self._guess_http_method(name, docstring, func)

            return OperationInfo(
                name=name,
                parameters=parameters,
                return_type=return_type,
                docstring=docstring,
                http_method=http_method,
                function=func,
            )

        except Exception:
            # If analysis fails, skip this operation
            return None

    def _guess_http_method(self, name: str, docstring: str | None, func: typing.Callable | None = None) -> str:
        """Guess the HTTP method from the operation name or docstring.

        Args:
            name: Operation name
            docstring: Operation docstring
            func: The function to inspect (for clientele decorator extraction)

        Returns:
            HTTP method string (GET, POST, PUT, PATCH, DELETE, or UNKNOWN)
        """
        # First try to extract from clientele decorator closure (for new clientele-based clients)
        if func is not None:
            method = self._extract_method_from_clientele_decorator(func)
            if method:
                return method

        name_lower = name.lower()

        # Check function name for HTTP method hints
        if any(x in name_lower for x in ["_get", "_list", "_retrieve", "_read"]):
            return "GET"
        elif "_post" in name_lower or "_create" in name_lower:
            return "POST"
        elif "_put" in name_lower or "_update" in name_lower:
            return "PUT"
        elif "_patch" in name_lower:
            return "PATCH"
        elif "_delete" in name_lower:
            return "DELETE"

        # Check docstring for HTTP method hints
        if docstring:
            doc_lower = docstring.lower()
            if "get " in doc_lower or "retrieve" in doc_lower or "fetch" in doc_lower:
                return "GET"
            elif "create" in doc_lower or "post " in doc_lower:
                return "POST"
            elif "update" in doc_lower or "put " in doc_lower:
                return "PUT"
            elif "patch" in doc_lower:
                return "PATCH"
            elif "delete" in doc_lower:
                return "DELETE"

        return "UNKNOWN"

    def _extract_method_from_clientele_decorator(self, func: typing.Callable) -> str | None:
        """Extract HTTP method from clientele decorator closure.

        For clientele-based clients using @client.get(), @client.post(), etc.,
        the decorator stores a _RequestContext object in the closure that contains
        the HTTP method.

        Args:
            func: The decorated function

        Returns:
            HTTP method string (GET, POST, etc.) or None if not found
        """
        try:
            # Check if the function has a closure (decorators create closures)
            if not hasattr(func, "__closure__"):
                return None

            closure = func.__closure__
            if closure is None:
                return None

            # Type narrowing: closure is guaranteed to be a tuple of cells at this point
            closure = typing.cast(tuple, closure)

            # Look through closure cells for _RequestContext
            for cell in closure:
                cell_contents = cell.cell_contents
                # Check if this is a _RequestContext (has method and path_template attributes)
                if hasattr(cell_contents, "__dict__"):
                    cell_dict = getattr(cell_contents, "__dict__", {})
                    # _RequestContext has both 'method' and 'path_template' attributes
                    if "method" in cell_dict and "path_template" in cell_dict:
                        # This looks like a _RequestContext
                        method = cell_dict.get("method")
                        if isinstance(method, str):
                            return method.upper()

        except (AttributeError, TypeError, KeyError):
            # If anything goes wrong during extraction, fail silently
            # This is expected for non-clientele clients
            pass

        return None

    def get_all_schemas(self) -> dict[str, typing.Any]:
        """Get all Pydantic schemas from the schemas module.

        Returns:
            Dictionary of schema name to schema class
        """
        if not self.schemas_module:
            return {}

        schemas = {}
        for name, obj in inspect.getmembers(self.schemas_module):
            # Skip private members and imports
            if name.startswith("_"):
                continue

            # Check if it's a Pydantic model
            if inspect.isclass(obj):
                # Check if it has model_fields (Pydantic v2) or __fields__ (Pydantic v1)
                if hasattr(obj, "model_fields") or hasattr(obj, "__fields__"):
                    schemas[name] = obj

        return schemas

    def get_schema_info(self, schema_name: str) -> dict[str, typing.Any] | None:
        """Get detailed information about a specific schema.

        Args:
            schema_name: Name of the schema to inspect

        Returns:
            Dictionary with schema information or None if not found
        """
        schemas = self.get_all_schemas()
        if schema_name not in schemas:
            return None

        schema_class = schemas[schema_name]
        # Use __doc__ directly instead of inspect.getdoc() to avoid inheriting
        # from parent classes (like pydantic.BaseModel's verbose docstring)
        docstring = schema_class.__doc__
        info: dict[str, typing.Any] = {
            "name": schema_name,
            "docstring": docstring,
            "fields": {},
        }

        # Get field information (Pydantic v2)
        if hasattr(schema_class, "model_fields"):
            for field_name, field_info in schema_class.model_fields.items():
                info["fields"][field_name] = {
                    "type": str(field_info.annotation) if hasattr(field_info, "annotation") else "Unknown",
                    "required": field_info.is_required() if hasattr(field_info, "is_required") else True,
                    "default": field_info.default if hasattr(field_info, "default") else None,
                    "description": field_info.description if hasattr(field_info, "description") else None,
                }
        # Fallback to Pydantic v1
        elif hasattr(schema_class, "__fields__"):
            for field_name, field_info in schema_class.__fields__.items():
                info["fields"][field_name] = {
                    "type": str(field_info.outer_type_) if hasattr(field_info, "outer_type_") else "Unknown",
                    "required": field_info.required,
                    "default": field_info.default,
                    "description": field_info.field_info.description if hasattr(field_info, "field_info") else None,
                }

        return info

    def get_client_instance(self) -> typing.Any:
        """Get the client instance for class-based clients.

        Returns:
            Client instance or None for function-based clients
        """
        return self.client_instance
