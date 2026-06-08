# 🚀 Install

Clientele has two installation options:

| Extra | What's included | Use when |
|---|---|---|
| `clientele` or `clientele[core]` | `httpx`, `pydantic`, `pydantic-settings`, `stamina` | Writing API clients in your own code |
| `clientele[cli]` | everything above + `click`, `rich`, `cicerone`, `jinja2`, `ruff`, `pyyaml` | Generating clients from OpenAPI schemas |

## Core install (default)

Install the core library to write and run API clients:

### uv

```sh
uv add clientele
# or explicitly:
uv add "clientele[core]"
```

### pip

```sh
pip install clientele
# or explicitly:
pip install "clientele[core]"
```

## CLI install

Install with the `cli` extra to use the `clientele` command-line tool and generate clients from OpenAPI schemas:

### uv

```sh
uv add "clientele[cli]"
```

### pip

```sh
pip install "clientele[cli]"
```

Once installed, you can run `clientele version` to confirm:

```sh
> clientele version
clientele 2.2.1
```

## Next steps

- [Clientele API guide](api-overview.md) to write your own API client
- [Client creator](openapi-cli.md) to quick start an API client from an OpenAPI schema (requires `clientele[cli]`)
- [API server integration](server-fastapi.md) to learn how to integrate with popular Python API servers
