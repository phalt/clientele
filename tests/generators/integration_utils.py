"""Shared utilities for generator integration tests."""

from __future__ import annotations

from pathlib import Path

from cicerone import parse as cicerone_parse

# Path to example OpenAPI specs directory
EXAMPLE_SPECS_DIR = Path(__file__).parents[2] / "example_openapi_specs"


def load_spec(spec_filename: str):
    """
    Load an OpenAPI spec from the example_openapi_specs directory.

    Args:
        spec_filename: Name of the spec file (e.g., 'simple.json', 'best.json')

    Returns:
        Loaded OpenAPI Spec object
    """
    spec_path = EXAMPLE_SPECS_DIR / spec_filename
    return cicerone_parse.parse_spec_from_file(str(spec_path))


def get_spec_path(spec_filename: str) -> Path:
    """
    Get the full path to a spec file in the example_openapi_specs directory.

    Args:
        spec_filename: Name of the spec file (e.g., 'simple.json', 'best.json')

    Returns:
        Path object pointing to the spec file
    """
    return EXAMPLE_SPECS_DIR / spec_filename
