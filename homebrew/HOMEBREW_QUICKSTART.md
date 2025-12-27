# Homebrew Installation - Quick Reference

**Goal:** Enable users to install clientele with `brew install phalt/clientele/clientele`

## ✅ What's Already Done

All the tooling is ready! The repository includes:
- ✅ Automatic formula generator (`homebrew/generate_formula.py`)
- ✅ Makefile commands (`brew-formula`, `brew-verify`, `brew-test-local`)
- ✅ Documentation (HOMEBREW_SETUP.md, HOMEBREW_PUBLISHING.md)
- ✅ Installation instructions in README.md

## 🎯 What You Need to Do

### One-Time Setup (Do This Once)

1. **Create a tap repository on GitHub:**
   - Repository name: `homebrew-clientele`
   - Organization/Owner: `phalt`
   - Full path: `https://github.com/phalt/homebrew-clientele`
   - Visibility: Public

2. **Initialize the tap:**
   ```bash
   git clone https://github.com/phalt/homebrew-clientele.git
   cd homebrew-clientele
   mkdir -p Formula
   echo "# Homebrew Tap for Clientele" > README.md
   git add .
   git commit -m "Initial tap setup"
   git push
   ```

### For Each Release (Repeat Every Time)

```bash
# 1. Release to PyPI (in clientele repository)
make release

# 2. Generate the Homebrew formula
make brew-formula

# 3. (Optional) Test locally
make brew-test-local

# 4. Copy to tap repository
cp homebrew/clientele.rb /path/to/homebrew-clientele/Formula/clientele.rb
cd /path/to/homebrew-clientele
git add Formula/clientele.rb
git commit -m "Update clientele to version X.Y.Z"
git push
```

## 📦 How Users Will Install

Once the tap is set up:

```bash
# Method 1: Single command
brew install phalt/clientele/clientele

# Method 2: Tap first, then install
brew tap phalt/clientele
brew install clientele
```

## 🔍 Quick Commands

```bash
make brew-status        # Check current status
make brew-formula       # Generate formula
make brew-verify        # Audit the formula
make brew-test-local    # Test installation locally
```

## 📚 Need More Details?

- **Step-by-step guide:** See [HOMEBREW_SETUP.md](HOMEBREW_SETUP.md)
- **Technical details:** See [HOMEBREW_PUBLISHING.md](HOMEBREW_PUBLISHING.md)
- **Tooling docs:** See [README.md](README.md)

## 🚀 TL;DR

1. Create `phalt/homebrew-clientele` repository on GitHub ← **YOU NEED TO DO THIS**
2. Set up the Formula directory
3. For each release: `make brew-formula` → copy to tap → commit & push

That's it! 🎉
