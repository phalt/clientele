# Homebrew Publishing Workflow

This document describes the workflow for publishing clientele to Homebrew.

> **📖 Looking for setup instructions?** See [HOMEBREW_SETUP.md](HOMEBREW_SETUP.md) for a simplified step-by-step guide.

## Prerequisites

1. Have a new version ready to release
2. Version must be updated in `pyproject.toml` and `clientele/settings.py`
3. Package must be published to PyPI

## Publishing Workflow

### 1. Release to PyPI

First, ensure your package is released to PyPI:

```bash
# Build and release to PyPI
make release
```

### 2. Generate the Homebrew Formula

After the PyPI release is live, generate the Homebrew formula:

```bash
# Generate the formula with correct versions and checksums
make brew-formula
```

This will create `homebrew/clientele.rb` with:
- Current version from `pyproject.toml`
- SHA256 checksums from PyPI
- All required dependencies

### 3. Verify the Formula (Optional)

If you have Homebrew installed:

```bash
# Run brew audit to check for issues
make brew-verify
```

### 4. Test Locally (Optional)

Test the installation locally:

```bash
# Install from the generated formula
make brew-test-local

# Verify it works
clientele version
```

### 5. Update Your Tap Repository

#### First Time Setup

If you haven't created a tap yet:

```bash
# Create a new repository on GitHub named: homebrew-clientele
# Clone it locally
git clone https://github.com/phalt/homebrew-clientele.git
cd homebrew-clientele

# Initialize the structure
mkdir -p Formula
cp /path/to/clientele/homebrew/clientele.rb Formula/clientele.rb
git add Formula/clientele.rb
git commit -m "Add clientele formula v0.9.0"
git push
```

#### Updating an Existing Tap

For subsequent releases:

```bash
# Copy the new formula
cp /path/to/clientele/homebrew/clientele.rb /path/to/homebrew-clientele/Formula/clientele.rb

# Commit and push
cd /path/to/homebrew-clientele
git add Formula/clientele.rb
git commit -m "Update clientele to version X.Y.Z"
git push
```

### 6. Announce the Release

Users can now install clientele via Homebrew:

```bash
brew tap phalt/clientele
brew install clientele
```

Or in a single command:

```bash
brew install phalt/clientele/clientele
```

## Troubleshooting

### Formula Generation Fails

**Problem:** Script fails to download package information

**Solution:**
- Ensure the version exists on PyPI
- Check your internet connection
- Verify package name is correct

### SHA256 Mismatch

**Problem:** Homebrew reports incorrect checksums

**Solution:**
- Delete `homebrew/clientele.rb`
- Run `make brew-formula` again
- PyPI might have been updated after initial download

### Missing Dependencies

**Problem:** Formula has unreplaced variables like `{{PACKAGE_VERSION}}`

**Solution:**
- Check the dependency is actually needed
- Add it to the `all_packages` list in `homebrew/generate_formula.py`
- Verify the package name matches PyPI (underscores vs hyphens)

### Installation Fails

**Problem:** `brew install` fails with dependency errors

**Solution:**
- Check all dependencies are in the formula
- Verify Python version compatibility
- Test with `make brew-test-local` first

## Automated Publishing (Future Enhancement)

Consider automating this workflow with GitHub Actions:

```yaml
name: Update Homebrew Formula

on:
  release:
    types: [published]

jobs:
  update-formula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Generate formula
        run: make brew-formula
      - name: Update tap
        run: |
          # Push to homebrew-clientele repository
          # This requires a GitHub token with repo access
```

## Best Practices

1. **Always test locally** before pushing to tap
2. **Version in sync**: Ensure `pyproject.toml`, `settings.py`, and PyPI match
3. **Document changes**: Update CHANGELOG.md for each release
4. **Keep dependencies current**: Regularly update to avoid security issues
5. **Monitor issues**: Watch for Homebrew installation problems

## References

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- [Creating Taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
