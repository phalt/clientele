
# Regeneration

At times you may wish to regenerate a client.

This could be because the API has updated or you just want to use a newer version of Clientele.

To force a regeneration you must pass the `--regen` or `-r` argument, for example:

```sh
clientele generate -f example_openapi_specs/best.json -o my_client/  --regen t
```

!!! note

    You can copy and paste the command from the `MANIFEST.md` file in your previously-generated client for a quick and easy regeneration.

## Understanding Regeneration

When you regenerate a client with `--regen t`, Clientele follows these rules:

**Files that WILL be overwritten:**

- `client.py` - Your API client functions/class
- `schemas.py` - Pydantic models for request/response data
- `http.py` - HTTP handling logic
- `__init__.py` - Package initialization
- `MANIFEST.md` - Metadata about the generated client

**Files that will NOT be overwritten:**

- `config.py` - Your custom configuration (API URL, auth tokens, headers)

This design ensures your customizations in `config.py` are preserved while keeping the client code in sync with the latest API schema.

## The MANIFEST.md File

Every generated client includes a `MANIFEST.md` file that records:

- The exact command used to generate the client
- The OpenAPI version of the source schema
- The Clientele version used
- Generation timestamp

Example `MANIFEST.md`:

    # Manifest

    Generated with [https://github.com/phalt/clientele](https://github.com/phalt/clientele)
    Install with pipx:

    ```sh
    pipx install clientele
    ```

    API VERSION: 0.1.0
    OPENAPI VERSION: 3.0.2
    CLIENTELE VERSION: 1.2.0

    Regenerate using this command:

    ```sh
    clientele generate -f example_openapi_specs/best.json -o tests/async_test_client/ --asyncio t --regen t
    ```

    Explore this API interactively:

    ```sh
    clientele explore -c .
    ```

## Regeneration Workflow

Here's the recommended workflow for keeping your client in sync:

1. **API Updated**: Your API has new endpoints or changed schemas
2. **Regenerate**: Run `clientele generate` with `--regen t`
```sh
clientele generate -u http://localhost:8000/openapi.json -o my_client/ --regen t
```
3. **Review Changes**: Use git to see what changed
```sh
git diff my_client/
```
4. **Inspect** the changes.
5. **Test**: Run your test suite to catch breaking changes
```sh
pytest tests/
```
6. **Commit**: Add the changes to git
```sh
git add my_client/
git commit -m "Regenerate client for API v2.1"
```

## Handling Breaking Changes

When the API introduces breaking changes, regeneration will reflect them:

- **Removed endpoints** → Functions deleted from `client.py`
- **Renamed fields** → Schema properties change
- **New required fields** → Function signatures updated
- **Changed response types** → Schema unions modified

You should have tests to catch these issues.

If you need to support multiple API versions, consider generating separate clients for each version sing version-specific directories (e.g., `my_client_v1/`, `my_client_v2/`).

## Integration with CI/CD

You can automate regeneration in CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Regenerate API client
  run: |
    clientele generate \
      -u http://api:8000/openapi.json \
      -o clients/my_api/ \
      --regen t
    
    # Check if client changed
    if ! git diff --quiet clients/my_api/; then
      echo "API client changed - review required"
      git diff clients/my_api/
      exit 1
    fi
```

This keeps your client in sync with the API schema.
