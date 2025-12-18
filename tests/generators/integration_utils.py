"""Shared utilities for generator integration tests."""

from pathlib import Path

from openapi_core import Spec

# Path to example OpenAPI specs directory
EXAMPLE_SPECS_DIR = Path(__file__).parents[2] / "example_openapi_specs"


def load_spec(spec_filename: str) -> Spec:
    """
    Load an OpenAPI spec from the example_openapi_specs directory.

    Args:
        spec_filename: Name of the spec file (e.g., 'simple.json', 'best.json')

    Returns:
        Loaded OpenAPI Spec object
    """
    spec_path = EXAMPLE_SPECS_DIR / spec_filename
    with open(spec_path, "r") as f:
        return Spec.from_file(f)


def get_spec_path(spec_filename: str) -> Path:
    """
    Get the full path to a spec file in the example_openapi_specs directory.

    Args:
        spec_filename: Name of the spec file (e.g., 'simple.json', 'best.json')

    Returns:
        Path object pointing to the spec file
    """
    return EXAMPLE_SPECS_DIR / spec_filename
