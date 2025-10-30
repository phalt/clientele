# Homebrew Publishing Guide for Clientele

This directory contains the tooling and templates needed to publish clientele on Homebrew (brew.sh).

## Overview

Homebrew is a popular package manager for macOS and Linux. Publishing clientele on Homebrew makes it accessible to a wider audience without requiring Python knowledge.

## Files

- `clientele.rb.template` - Template for the Homebrew formula with placeholders
- `generate_formula.py` - Python script to generate the formula with correct versions and checksums
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
2. Fetch package information from PyPI
3. Download and verify checksums for all dependencies
4. Generate `homebrew/clientele.rb` from the template

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

If the generated formula has unreplaced variables (like `{{SOME_PACKAGE_VERSION}}`):

1. Check if the dependency is actually needed
2. Update `generate_formula.py` to include it in the `all_packages` list
3. Verify the package name on PyPI (it might be different)

### Formula Audit Fails

Run `make brew-verify` to see specific issues. Common problems:

- Incorrect SHA256 checksums
- Invalid URLs
- Missing dependencies
- Ruby syntax errors

### Installation Test Fails

- Ensure all dependencies are included in the formula
- Check that the entry point is correct (`clientele = "clientele.cli:cli_group"`)
- Verify the package installs correctly from PyPI

## Formula Structure

The formula uses Homebrew's `virtualenv_install_with_resources` helper, which:

1. Creates an isolated Python virtual environment
2. Installs the main package and all its dependencies
3. Links the CLI command to `/usr/local/bin/clientele`

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
