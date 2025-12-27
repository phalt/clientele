# Setting Up Homebrew Installation for Clientele

This guide explains how to enable users to install clientele via Homebrew (`brew install clientele`).

## Current Status

✅ **All tooling is ready!** The repository already includes:
- Automatic formula generator (`homebrew/generate_formula.py`)
- Makefile commands for easy workflow
- Comprehensive documentation

❌ **What's missing:**
- A Homebrew tap repository (one-time setup)
- Generated formula for the current version
- Instructions in the main README

## Quick Overview

Homebrew installation works through a "tap" - a third-party repository containing Homebrew formulas. Here's the complete workflow:

1. **One-time setup**: Create a tap repository on GitHub
2. **For each release**: Generate and publish the formula to your tap

## One-Time Setup: Create Your Tap

A "tap" is simply a GitHub repository with a specific naming convention.

### Step 1: Create the Tap Repository

1. Go to GitHub and create a new repository named `homebrew-clientele` in the `phalt` organization
   - Full name will be: `phalt/homebrew-clientele`
   - Make it public
   - Initialize with a README if you want

### Step 2: Set Up the Tap Structure

```bash
# Clone the new tap repository
git clone https://github.com/phalt/homebrew-clientele.git
cd homebrew-clientele

# Create the Formula directory (required by Homebrew)
mkdir -p Formula

# Add a README explaining what this is
cat > README.md << 'EOF'
# Homebrew Tap for Clientele

This repository contains the Homebrew formula for [clientele](https://github.com/phalt/clientele), the Python API Client Generator.

## Installation

```bash
brew install phalt/clientele/clientele
```

Or:

```bash
brew tap phalt/clientele
brew install clientele
```

## About

This tap is automatically updated with each clientele release. For more information, see the [main repository](https://github.com/phalt/clientele).
EOF

# Commit and push
git add README.md Formula/
git commit -m "Initial tap setup"
git push
```

That's it! Your tap is ready. Now you just need to add formulas to it.

## Publishing Workflow (For Each Release)

Every time you release a new version of clientele, follow these steps:

### Step 1: Release to PyPI

```bash
# In the clientele repository
make release
```

Wait for PyPI to process the upload (usually takes a few minutes).

### Step 2: Generate the Homebrew Formula

```bash
# Still in the clientele repository
make brew-formula
```

This will:
- Read the version from `pyproject.toml`
- Download the package from PyPI
- Calculate checksums for all dependencies
- Generate `homebrew/clientele.rb`

### Step 3: Verify the Formula (Optional but Recommended)

If you have Homebrew installed:

```bash
make brew-verify        # Check for issues
make brew-test-local    # Test installation locally
```

### Step 4: Update Your Tap

```bash
# Copy the generated formula to your tap
cp /path/to/clientele/homebrew/clientele.rb /path/to/homebrew-clientele/Formula/clientele.rb

# Commit and push to the tap
cd /path/to/homebrew-clientele
git add Formula/clientele.rb
git commit -m "Update clientele to version $(grep 'version = ' Formula/clientele.rb | head -1 | cut -d'"' -f2)"
git push
```

### Step 5: Announce

Update your release notes or announcements to include:

```bash
# Install via Homebrew
brew install phalt/clientele/clientele
```

## User Installation

Once your tap is set up and has a formula, users can install clientele with:

```bash
# One-time: Add your tap
brew tap phalt/clientele

# Install clientele
brew install clientele
```

Or in a single command:

```bash
brew install phalt/clientele/clientele
```

## Troubleshooting

### "Version not found on PyPI"

**Problem**: `make brew-formula` fails because it can't find the version on PyPI.

**Solution**: 
- Verify you ran `make release` and it completed successfully
- Wait a few minutes for PyPI to process the upload
- Check https://pypi.org/project/clientele/ to confirm the version exists

### "Unreplaced variables in formula"

**Problem**: The generated formula contains `{{PACKAGE_VERSION}}` placeholders.

**Solution**:
- Check if the dependency is actually needed
- Add it to the `all_packages` list in `homebrew/generate_formula.py`
- Verify the package name matches PyPI (check underscores vs hyphens)

### Formula audit fails

**Problem**: `make brew-verify` reports errors.

**Solution**:
- Check the specific error message from `brew audit`
- Common issues:
  - Incorrect checksums (regenerate with `make brew-formula`)
  - Invalid URLs (check package is on PyPI)
  - Ruby syntax errors (review the generated formula)

## Automation Ideas

### GitHub Actions (Future Enhancement)

You can automate the formula update process:

```yaml
# .github/workflows/update-homebrew.yml
name: Update Homebrew Formula

on:
  release:
    types: [published]

jobs:
  update-formula:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install httpx tomli
      
      - name: Generate formula
        run: make brew-formula
      
      - name: Update tap
        env:
          TAP_TOKEN: ${{ secrets.TAP_TOKEN }}
        run: |
          git clone https://x-access-token:${TAP_TOKEN}@github.com/phalt/homebrew-clientele.git tap
          cp homebrew/clientele.rb tap/Formula/clientele.rb
          cd tap
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add Formula/clientele.rb
          git commit -m "Update clientele to version ${{ github.event.release.tag_name }}"
          git push
```

This would automatically update your tap whenever you create a GitHub release.

## Best Practices

1. **Always test locally** before pushing to the tap
2. **Keep versions in sync** across `pyproject.toml`, `settings.py`, and PyPI
3. **Document in release notes** that Homebrew installation is available
4. **Monitor for issues** - users may report installation problems
5. **Update promptly** - keep the formula current with each release

## Summary: What You Need to Do

### First Time Only:
1. Create GitHub repository: `phalt/homebrew-clientele`
2. Set up the Formula directory structure
3. Update main README with Homebrew installation instructions

### For Every Release:
1. `make release` (publish to PyPI)
2. `make brew-formula` (generate the formula)
3. Copy formula to tap repository
4. Commit and push to tap

That's it! The infrastructure is all ready - you just need to create the tap repository and start using it.

## Additional Resources

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Creating Taps](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap)
- [Python Formula Guide](https://docs.brew.sh/Python-for-Formula-Authors)
- See `HOMEBREW_PUBLISHING.md` for more detailed technical information
