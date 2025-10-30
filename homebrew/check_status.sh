#!/bin/bash
# Check the status of Homebrew publishing setup

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🍺 Homebrew Publishing Status Check"
echo "===================================="
echo ""

# Check pyproject.toml version
PYPROJECT_VERSION=$(grep '^version = ' "$REPO_ROOT/pyproject.toml" | cut -d'"' -f2)
echo "📦 Current version in pyproject.toml: $PYPROJECT_VERSION"

# Check settings.py version
SETTINGS_VERSION=$(grep '^VERSION = ' "$REPO_ROOT/clientele/settings.py" | cut -d'"' -f2)
echo "📦 Current version in settings.py: $SETTINGS_VERSION"

# Check if versions match
if [ "$PYPROJECT_VERSION" = "$SETTINGS_VERSION" ]; then
    echo "✅ Versions are in sync"
else
    echo "❌ Versions are out of sync!"
    echo "   Please update both files to the same version before releasing."
    exit 1
fi

# Check if formula exists
if [ -f "$SCRIPT_DIR/clientele.rb" ]; then
    FORMULA_VERSION=$(grep 'url "https://files.pythonhosted.org/packages/source/c/clientele/clientele-' "$SCRIPT_DIR/clientele.rb" | sed -n 's/.*clientele-\([0-9][0-9.]*\)\.tar\.gz.*/\1/p')
    echo "🍺 Homebrew formula exists: v$FORMULA_VERSION"
    
    if [ "$PYPROJECT_VERSION" = "$FORMULA_VERSION" ]; then
        echo "✅ Formula version matches current version"
    else
        echo "⚠️  Formula version ($FORMULA_VERSION) does not match current version ($PYPROJECT_VERSION)"
        echo "   Run 'make brew-formula' to regenerate the formula"
    fi
else
    echo "⚠️  Homebrew formula not generated yet"
    echo "   Run 'make brew-formula' to generate it"
fi

echo ""

# Check if package is on PyPI
echo "🔍 Checking PyPI..."
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "https://pypi.org/pypi/clientele/$PYPROJECT_VERSION/json")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "✅ Version $PYPROJECT_VERSION is available on PyPI"
    else
        echo "⚠️  Version $PYPROJECT_VERSION is not on PyPI yet"
        echo "   Run 'make release' to publish to PyPI before generating the formula"
    fi
else
    echo "⚠️  curl not available, skipping PyPI check"
fi

echo ""
echo "📚 Next steps:"
echo "   1. Ensure version is released to PyPI: make release"
echo "   2. Generate Homebrew formula: make brew-formula"
echo "   3. Verify formula (if Homebrew installed): make brew-verify"
echo "   4. Update your tap repository with the new formula"
echo ""
echo "📖 See HOMEBREW_PUBLISHING.md for detailed instructions"
