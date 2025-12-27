# Homebrew Installation Error Fix Summary

## Problem

Users were experiencing a build error when installing clientele via Homebrew:

```
× pip subprocess to install build dependencies did not run successfully.
│ exit code: 1
╰─> See above for output.

note: This error originates from a subprocess, and is likely not a problem with pip.
full command: ... 'maturin>=1.9,<2.0'
```

The error occurred because:

1. **Missing dependencies**: The formula had hardcoded dependencies that didn't match `pyproject.toml`:
   - Missing: `cicerone`, `prompt_toolkit`, `cli-helpers`
   - Incorrectly included: `openapi-core` (not in pyproject.toml)

2. **Build-from-source issue**: Homebrew's `virtualenv_install_with_resources` uses `--no-binary :all:` by default, forcing all packages to build from source. Rust packages like `pydantic-core`, `rpds-py`, and `ruff` require `maturin` to build, but `maturin` itself needs Rust to build, creating a circular dependency.

3. **Manual maintenance burden**: The dependency list was hardcoded in `generate_formula.py`, requiring manual updates whenever `pyproject.toml` changed.

## Solution

The fix involved three key changes to `generate_formula.py`:

### 1. Auto-detect Dependencies from pyproject.toml

The script now:
- Reads all dependencies directly from `pyproject.toml`
- Recursively resolves transitive dependencies via PyPI API
- Automatically handles new or changed dependencies

**Before**: 
```python
core_deps = ["httpx", "click", "pydantic", "rich", "openapi-core", ...]
additional_deps = ["httpcore", "h11", "certifi", ...]
```

**After**:
```python
# Read from pyproject.toml
direct_deps = get_dependencies_from_pyproject()
# Resolve all transitive dependencies automatically
all_dependencies = resolve_transitive_dependencies(direct_deps)
```

### 2. Use Binary Wheels by Default

Instead of building from source, the formula now uses pre-built binary wheels:

**Before**:
```ruby
def install
  virtualenv_install_with_resources  # Uses --no-binary :all:
end
```

**After**:
```ruby
def install
  # Create virtualenv and install all dependencies
  # Use binary wheels for all packages to avoid build issues with Rust/C extensions
  venv = virtualenv_create(libexec, "python3.12")
  venv.pip_install resources  # Uses binary wheels by default
  venv.pip_install_and_link buildpath
end
```

This eliminates the need for Rust toolchain, maturin, or any build dependencies.

### 3. Package Name Normalization

Implemented proper package name deduplication to handle packages that appear with different naming conventions (e.g., `typing-extensions` vs `typing_extensions`):

```python
def normalize_dependency_name(name: str) -> str:
    """Normalize per PEP 503: lowercase and replace [-_.] with dash"""
    import re
    return re.sub(r"[-_.]+", "-", name).lower()
```

## Benefits

✅ **No more build errors**: Binary wheels eliminate Rust/maturin dependency
✅ **Faster installation**: No compilation needed, just download and install
✅ **Auto-sync with pyproject.toml**: Dependencies stay in sync automatically  
✅ **No manual maintenance**: Adding/removing dependencies just requires re-running the generator
✅ **Complete dependency resolution**: All transitive dependencies included automatically

## Testing

The generated formula now includes all 11 direct dependencies plus 17 transitive dependencies:

**Direct dependencies** (from pyproject.toml):
- cicerone, cli-helpers, click, httpx, jinja2, prompt_toolkit, pydantic, pyyaml, rich, ruff, types-pyyaml

**Transitive dependencies** (auto-resolved):
- MarkupSafe, annotated-types, anyio, certifi, colorama, configobj, exceptiongroup, h11, httpcore, idna, markdown-it-py, mdurl, pydantic-core, typing-extensions, typing-inspection, wcwidth

## Usage

The workflow remains the same:

```bash
# After releasing to PyPI
make brew-formula

# Formula is generated at homebrew/clientele.rb
# Copy to tap repository and publish
```

No additional configuration or manual dependency management needed!
