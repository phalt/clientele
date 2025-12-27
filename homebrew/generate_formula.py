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


def get_dependencies_from_pyproject() -> list[str]:
    """Extract dependency names from pyproject.toml."""
    assert toml_loader is not None, "tomllib/tomli is required but not available"
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = toml_loader.load(f)

    dependencies: list[str] = []
    for dep in data["project"]["dependencies"]:
        # Extract package name, handling various version specifiers
        # Split on common version operators
        for sep in [">=", "==", "<=", ">", "<", "~=", "!="]:
            if sep in dep:
                name = dep.split(sep)[0].strip()
                break
        else:
            # Handle complex specifiers with commas (e.g., "package>=1.0,<2.0")
            if "," in dep:
                name = dep.split(",")[0]
                for sep in [">=", "==", "<=", ">", "<", "~=", "!="]:
                    if sep in name:
                        name = name.split(sep)[0].strip()
                        break
            else:
                name = dep.strip()

        dependencies.append(name)

    return dependencies


def normalize_dependency_name(name: str) -> str:
    """Normalize dependency name for deduplication (PyPI canonical form)."""
    # Per PEP 503, package names should be normalized:
    # lowercase and replace runs of [-_.] with a single dash
    import re

    return re.sub(r"[-_.]+", "-", name).lower()


def get_transitive_dependencies(package_name: str, version: str, visited: set[str] | None = None) -> dict[str, str]:
    """Recursively get all transitive dependencies from PyPI metadata."""
    if visited is None:
        visited = set()

    # Normalize package name for deduplication
    normalized_name = normalize_dependency_name(package_name)

    if normalized_name in visited:
        return {}

    visited.add(normalized_name)
    all_deps: dict[str, str] = {}

    try:
        info = get_package_info(package_name, version)
        # Use the actual package name from PyPI, not the normalized one
        actual_name = package_name
        all_deps[actual_name] = info["version"]

        # Get package metadata to find dependencies
        response = httpx.get(f"https://pypi.org/pypi/{package_name}/{info['version']}/json", timeout=30.0)
        response.raise_for_status()
        data = response.json()

        # Parse requires_dist
        requires = data["info"].get("requires_dist", []) or []
        for req in requires:
            # Skip optional dependencies (those with ; markers for extras)
            if ";" in req and "extra ==" in req:
                continue

            # Extract package name
            req = req.split(";")[0].strip()  # Remove environment markers
            dep_name = req.split()[0].strip()  # Get first word (package name)

            # Remove any version specifiers from name
            for sep in [">=", "==", "<=", ">", "<", "~=", "!=", "["]:
                if sep in dep_name:
                    dep_name = dep_name.split(sep)[0].strip()
                    break

            # Recursively get transitive dependencies
            if dep_name and normalize_dependency_name(dep_name) not in visited:
                try:
                    transitive = get_transitive_dependencies(dep_name, None, visited)  # type: ignore[arg-type]
                    all_deps.update(transitive)
                except Exception as e:
                    print(f"  Warning: Could not resolve {dep_name}: {e}")

    except Exception as e:
        print(f"  Warning: Could not get dependencies for {package_name}: {e}")

    return all_deps


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

    # Get direct dependencies from pyproject.toml
    print("\nReading dependencies from pyproject.toml...")
    direct_deps = get_dependencies_from_pyproject()
    print(f"Found {len(direct_deps)} direct dependencies: {', '.join(direct_deps)}")

    # Packages that require binary wheels (Rust/C extensions that are hard to build)
    # These will be marked specially in the formula
    BINARY_ONLY_PACKAGES = {
        "pydantic-core",  # Rust package, requires maturin
        "rpds-py",  # Rust package, requires maturin
        "ruff",  # Rust package, requires maturin
    }

    # Collect all dependencies (direct + transitive)
    print("\nResolving all transitive dependencies...")
    all_dependencies: dict[str, dict[str, str]] = {}  # normalized_name -> {version, actual_name}

    for dep_name in direct_deps:
        print(f"\nResolving {dep_name}...")
        try:
            transitive = get_transitive_dependencies(dep_name, None)  # type: ignore[arg-type]
            # Merge, avoiding duplicates by normalizing names
            for pkg, ver in transitive.items():
                normalized = normalize_dependency_name(pkg)
                if normalized not in all_dependencies:
                    all_dependencies[normalized] = {"version": ver, "actual_name": pkg}
        except Exception as e:
            print(f"Warning: Could not fully resolve {dep_name}: {e}")
            # At minimum, add the package itself
            try:
                info = get_package_info(dep_name, None)
                normalized = normalize_dependency_name(dep_name)
                if normalized not in all_dependencies:
                    all_dependencies[normalized] = {"version": info["version"], "actual_name": dep_name}
            except Exception as e2:
                print(f"Error: Could not fetch {dep_name}: {e2}")

    # Remove the main package from dependencies
    all_dependencies.pop(normalize_dependency_name("clientele"), None)

    print(f"\nTotal unique dependencies to include: {len(all_dependencies)}")

    # Fetch detailed info for all dependencies
    resources_data = []
    for normalized_name in sorted(all_dependencies.keys()):
        pkg_data = all_dependencies[normalized_name]
        package = pkg_data["actual_name"]
        pkg_version = pkg_data["version"]
        try:
            info = get_package_info(package, pkg_version)

            # Check if package needs binary wheels
            is_binary_only = normalize_dependency_name(package) in {
                normalize_dependency_name(p) for p in BINARY_ONLY_PACKAGES
            }

            resources_data.append(
                {
                    "name": package,
                    "version": info["version"],
                    "url": info["url"],
                    "sha256": info["sha256"],
                    "binary_only": is_binary_only,
                }
            )

        except Exception as e:
            print(f"Warning: Could not fetch info for {package}: {e}")

    # Generate the formula programmatically instead of using template
    print("\nGenerating Homebrew formula...")

    formula_lines = []
    formula_lines.append("class Clientele < Formula")
    formula_lines.append("  include Language::Python::Virtualenv")
    formula_lines.append("")
    formula_lines.append(
        '  desc "The Python API Client Generator for FastAPI, Django REST Framework, and Django Ninja"'
    )
    formula_lines.append('  homepage "https://phalt.github.io/clientele/"')
    formula_lines.append(f'  url "{clientele_info["url"]}"')
    formula_lines.append(f'  sha256 "{clientele_info["sha256"]}"')
    formula_lines.append('  license "MIT"')
    formula_lines.append("")
    formula_lines.append('  depends_on "python@3.12"')
    formula_lines.append('  depends_on "rust" => :build  # Required for pydantic-core and ruff')
    formula_lines.append("")

    # Add all resources
    for resource in sorted(resources_data, key=lambda x: x["name"]):
        formula_lines.append(f'  resource "{resource["name"]}" do')
        formula_lines.append(f'    url "{resource["url"]}"')
        formula_lines.append(f'    sha256 "{resource["sha256"]}"')
        formula_lines.append("  end")
        formula_lines.append("")

    # Install section
    formula_lines.append("  def install")
    formula_lines.append("    virtualenv_install_with_resources")
    formula_lines.append("  end")
    formula_lines.append("")
    formula_lines.append("  test do")
    formula_lines.append('    system bin/"clientele", "version"')
    formula_lines.append("  end")
    formula_lines.append("end")

    formula = "\n".join(formula_lines)

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
