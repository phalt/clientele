# Homebrew Publishing Guide for Clientele

This directory contains the tooling and templates needed to publish clientele on Homebrew (brew.sh).

> **📖 New to Homebrew publishing?** See [HOMEBREW_SETUP.md](HOMEBREW_SETUP.md) for a complete step-by-step setup guide.

> **✨ Recent Fix**: The formula generator now automatically detects all dependencies from `pyproject.toml` and includes Rust as a build dependency for packages like pydantic-core and ruff. No manual dependency management needed!

## Overview

Homebrew is a popular package manager for macOS and Linux. Publishing clientele on Homebrew makes it accessible to a wider audience without requiring Python knowledge.

## Files

- `generate_formula.py` - Python script to auto-generate the formula with all dependencies
- `clientele.rb` - Generated Homebrew formula (created by running the script)

## Quick Start

### Prerequisites

1. Ensure you have released the current version to PyPI (via `make release`)
2. The version in `pyproject.toml` should match the PyPI release

### Generate the Formula

```bash
make brew-formula
```

This will:
1. Read the current version from `pyproject.toml`
2. Fetch the package from PyPI  
3. Auto-detect all dependencies from `pyproject.toml`
4. Recursively resolve all transitive dependencies from PyPI
5. Calculate SHA256 checksums for all packages
6. Generate `homebrew/clientele.rb` with all resources

### Verify the Formula (Optional)

If you have Homebrew installed locally:

```bash
make brew-verify
```

This runs `brew audit` to check for common issues in the formula.

### Test Locally (Optional)

To test the installation locally:

```bash
make brew-test-local
```

This will install clientele from the generated formula and verify it works.

## Publishing to Homebrew

There are two main ways to publish on Homebrew:

### Option 1: Create Your Own Tap (Recommended for Third-Party Packages)

A "tap" is a third-party repository of Homebrew formulae.

1. **Create a new GitHub repository** named `homebrew-clientele` under your account (e.g., `phalt/homebrew-clientele`)

2. **Initialize the tap structure**:
   ```bash
   mkdir -p Formula
   cp homebrew/clientele.rb Formula/clientele.rb
   git init
   git add Formula/clientele.rb
   git commit -m "Add clientele formula"
   git remote add origin https://github.com/phalt/homebrew-clientele.git
   git push -u origin main
   ```

3. **Users can now install clientele via**:
   ```bash
   brew tap phalt/clientele
   brew install clientele
   ```

4. **Update the formula** when releasing new versions:
   ```bash
   # After releasing new version to PyPI
   make brew-formula
   cp homebrew/clientele.rb /path/to/homebrew-clientele/Formula/clientele.rb
   cd /path/to/homebrew-clientele
   git add Formula/clientele.rb
   git commit -m "Update clientele to version X.Y.Z"
   git push
   ```

### Option 2: Submit to Homebrew Core (More Complex)

To be included in the main Homebrew repository:

1. **Create a fork** of [homebrew-core](https://github.com/Homebrew/homebrew-core)

2. **Add the formula**:
   ```bash
   cp homebrew/clientele.rb /path/to/homebrew-core/Formula/c/clientele.rb
   ```

3. **Create a Pull Request** following [Homebrew's contribution guidelines](https://docs.brew.sh/Formula-Cookbook)

4. **Requirements for acceptance**:
   - The project should be notable (have significant usage/stars)
   - Active maintenance
   - Pass all Homebrew CI checks
   - Follow Homebrew best practices

## Updating the Formula

When you release a new version:

1. **Release to PyPI first**:
   ```bash
   make release
   ```

2. **Update version in `pyproject.toml`** if not already done

3. **Regenerate the formula**:
   ```bash
   make brew-formula
   ```

4. **Review the changes**:
   ```bash
   git diff homebrew/clientele.rb
   ```

5. **Update your tap repository** (if using Option 1)

## Troubleshooting

### Formula Generation Fails

- Ensure the version exists on PyPI
- Check your internet connection (script downloads packages)
- Verify `pyproject.toml` is valid

### Dependencies Missing

The formula generator automatically detects all dependencies from `pyproject.toml` and resolves their transitive dependencies from PyPI. No manual configuration needed!

If a dependency is missing:

1. Check if it's listed in `pyproject.toml`
2. Verify the package exists on PyPI
3. Re-run `make brew-formula` to regenerate

### Formula Audit Fails

Run `make brew-verify` to see specific issues. Common problems:

- Incorrect SHA256 checksums (regenerate with `make brew-formula`)
- Invalid URLs (check package is on PyPI)
- Missing dependencies (ensure all are in `pyproject.toml`)
- Ruby syntax errors (review the generated formula)

### Installation Test Fails

- Ensure all dependencies are included in `pyproject.toml`
- Check that the entry point is correct (`clientele = "clientele.cli:cli_group"`)
- Verify the package installs correctly from PyPI
- Rust build dependency is included for packages that need it (pydantic-core, ruff)

## Formula Structure

The formula uses Homebrew's standard `virtualenv_install_with_resources` method:

1. Creates an isolated Python 3.12 virtual environment
2. Installs all dependencies and the main package from source
3. Rust is included as a build dependency for packages that require it (pydantic-core, ruff)
4. Links the CLI command to the Homebrew bin directory

**Key Feature**: The formula uses Homebrew's standard installation method which builds packages from source. Rust is automatically included as a build dependency to compile Rust-based Python packages.

## How Dependencies Are Managed

The `generate_formula.py` script automatically:

1. **Reads** `pyproject.toml` to get all direct dependencies
2. **Resolves** transitive dependencies by querying PyPI metadata recursively
3. **Deduplicates** packages (handles both `package-name` and `package_name` variants)
4. **Fetches** SHA256 checksums for all packages from PyPI
5. **Generates** the complete Ruby formula with all resources

This means:
- ✅ No manual dependency list maintenance
- ✅ Always up-to-date with `pyproject.toml`
- ✅ Automatic handling of new dependencies
- ✅ No risk of missing transitive dependencies

## Best Practices

1. **Always test locally** before publishing
2. **Keep the tap updated** with each release
3. **Document the installation process** in the main README
4. **Monitor issues** related to Homebrew installation
5. **Keep dependencies minimal** - only include what's necessary

## Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- [Creating Taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Acceptable Formulae](https://docs.brew.sh/Acceptable-Formulae)

## Support

If users encounter issues with Homebrew installation:

1. Check the formula is up to date
2. Verify they're using the latest Homebrew (`brew update`)
3. Check for conflicting Python installations
4. Review Homebrew logs (`brew --prefix`/var/log/homebrew/)
