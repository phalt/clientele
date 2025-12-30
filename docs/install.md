# 🏗️ Install

We recommend installing Clientele as either a global tool or as a dev dependency.

## Global tool

Install Clientele as a global tool to get these benefits:

- Use across multiple projects
- Use to quickly explore and test APIs

### With uv

```sh
uv tool install clientele
```

### With pipx (Python)

```sh
pipx install clientele
```

### With Homebrew (macOS/Linux)

```sh
brew install phalt/clientele/clientele
```

## Dev dependency

Clientele does **not need to be to a production dependency** because it only produces code.

However it can be installed as a dev dependency to get these benefits:

- The whole team can use clientele to maintain a client library
- The whole team can use the explorer to test and debug the API

### uv

```sh
uv add --dev clientele
```

### pip

```sh
pip install clientele
```

Once installed, you can run `clientele version` to make sure you have the latest version:

```sh
> clientele version
clientele 1.2.0
```
