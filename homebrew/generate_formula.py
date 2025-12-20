#!/usr/bin/env python3
"""
Generate Homebrew formula for clientele with correct checksums.

This script:
1. Reads the current version from pyproject.toml
2. Downloads the package and all dependencies from PyPI
3. Calculates SHA256 checksums
4. Generates the Homebrew formula from the template
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from typing import IO, Any, Protocol

import httpx


class TomlLoader(Protocol):
    """Protocol for TOML loaders (tomllib or tomli)."""

    def load(self, fp: IO[bytes]) -> dict[str, Any]: ...


# Handle tomllib/tomli imports for different Python versions
if sys.version_info >= (3, 11):
    import tomllib

    toml_loader: TomlLoader = tomllib
else:
    try:
        import tomli  # type: ignore[import-not-found]

        toml_loader: TomlLoader = tomli
    except ImportError:
        toml_loader = None  # type: ignore[assignment]


def get_sha256_from_url(url: str) -> str:
    """Download a file and return its SHA256 hash."""
    print(f"Downloading {url}...")
    response = httpx.get(url, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    return hashlib.sha256(response.content).hexdigest()


def get_package_info(package_name: str, version: str | None = None) -> dict:
    """Get package information from PyPI."""
    print(f"Fetching info for {package_name}...")
    url = f"https://pypi.org/pypi/{package_name}/json"
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()
    data = response.json()

    if version:
        if version not in data["releases"]:
            raise ValueError(f"Version {version} not found for {package_name}")
        release = data["releases"][version]
    else:
        version = data["info"]["version"]
        release = data["releases"][version]

    # Find the source distribution
    for file_info in release:
        if file_info["packagetype"] == "sdist":
            return {
                "version": version,
                "url": file_info["url"],
                "sha256": file_info["digests"]["sha256"],
            }

    raise ValueError(f"No source distribution found for {package_name} {version}")


def normalize_package_name(name: str) -> str:
    """Normalize package name for template variables."""
    # Convert to uppercase and replace hyphens with underscores
    return name.upper().replace("-", "_")


def get_dependencies_from_pyproject() -> dict[str, str | None]:
    """Extract dependencies and their versions from pyproject.toml."""
    assert toml_loader is not None, "tomllib/tomli is required but not available"
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = toml_loader.load(f)

    dependencies: dict[str, str | None] = {}
    for dep in data["project"]["dependencies"]:
        if ">=" in dep:
            name, version = dep.split(">=")
            # For >= versions, we'll use None to get the latest compatible version
            dependencies[name.strip()] = None
        elif "==" in dep:
            name, version = dep.split("==")
            dependencies[name.strip()] = version.strip()
        else:
            # No version specified, will fetch latest
            dependencies[dep.strip()] = None

    return dependencies


def main():
    """Generate the Homebrew formula."""
    assert toml_loader is not None, "tomllib/tomli is required but not available"
    # Read current version
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = toml_loader.load(f)

    version = pyproject["project"]["version"]
    print(f"Generating Homebrew formula for clientele version {version}")

    # Get main package info
    clientele_info = get_package_info("clientele", version)

    # Start with the main package
    template_vars = {
        "VERSION": version,
        "SHA256": clientele_info["sha256"],
    }

    # Get all dependencies
    dependencies = get_dependencies_from_pyproject()

    # Core dependencies that need to be in the formula
    core_deps = ["httpx", "click", "pydantic", "rich", "openapi-core", "pyyaml", "jinja2", "ruff", "types-pyyaml"]

    # Additional transitive dependencies needed
    additional_deps = [
        "httpcore",
        "h11",
        "certifi",
        "idna",
        "sniffio",
        "anyio",
        "pydantic-core",
        "typing-extensions",
        "annotated-types",
        "markdown-it-py",
        "mdurl",
        "pygments",
        "openapi-schema-validator",
        "openapi-spec-validator",
        "jsonschema",
        "jsonschema-path",
        "jsonschema-specifications",
        "referencing",
        "rpds-py",
        "attrs",
        "markupsafe",
        "isodate",
        "werkzeug",
        "pathable",
        "lazy-object-proxy",
        "more-itertools",
        "rfc3339-validator",
    ]

    all_packages = core_deps + additional_deps

    # Fetch info for all dependencies
    for package in all_packages:
        try:
            # Get the version from pyproject.toml if available
            specified_version = dependencies.get(package)
            info = get_package_info(package, specified_version)

            var_prefix = normalize_package_name(package)
            template_vars[f"{var_prefix}_VERSION"] = info["version"]
            template_vars[f"{var_prefix}_SHA256"] = info["sha256"]
        except Exception as e:
            print(f"Warning: Could not fetch info for {package}: {e}")
            print("You may need to add this dependency manually or remove it from the template.")

    # Read template
    template_path = Path(__file__).parent / "clientele.rb.template"
    with open(template_path, "r") as f:
        template = f.read()

    # Replace all variables
    formula = template
    for key, value in template_vars.items():
        formula = formula.replace(f"{{{{{key}}}}}", value)

    # Check if there are any unreplaced variables
    if "{{" in formula:
        print("\nWarning: Some variables were not replaced:")
        import re

        unreplaced = re.findall(r"\{\{([^}]+)\}\}", formula)
        for var in unreplaced:
            print(f"  - {var}")
        print("\nYou may need to fetch these dependencies manually.")

    # Write output
    output_path = Path(__file__).parent / "clientele.rb"
    with open(output_path, "w") as f:
        f.write(formula)

    print(f"\n✅ Formula generated successfully: {output_path}")
    print("\nNext steps:")
    print("1. Review the formula at homebrew/clientele.rb")
    print("2. Test it locally with: brew install --build-from-source homebrew/clientele.rb")
    print("3. Create a tap repository on GitHub (e.g., phalt/homebrew-clientele)")
    print("4. Copy clientele.rb to Formula/clientele.rb in your tap")
    print("5. Users can then install with: brew tap phalt/clientele && brew install clientele")


if __name__ == "__main__":
    # Check if required packages are installed
    try:
        import httpx  # noqa: F401

        # Verify tomllib/tomli is available
        if toml_loader is None:
            raise ImportError("tomli")
    except ImportError as e:
        print(f"Error: Missing required package: {e}")
        print("Please run: pip install httpx")
        print("For Python < 3.11, also install: pip install tomli")
        sys.exit(1)

    main()
