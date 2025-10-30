import pathlib

import jinja2

templates = jinja2.Environment(loader=jinja2.PackageLoader("clientele", "generators/classbase/templates/"))

# Buffer to accumulate content before writing
_client_buffer: list[str] = []
_schemas_buffer: list[str] = []


def write_to_schemas(content: str, output_dir: str) -> None:
    """Write schema content immediately to file"""
    path = pathlib.Path(output_dir) / "schemas.py"
    _write_to(path, content)


def write_to_http(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "http.py"
    _write_to(path, content)


def write_to_client(content: str, output_dir: str) -> None:
    """Buffer client content for later writing"""
    _client_buffer.append(content)


def write_to_manifest(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "MANIFEST.md"
    _write_to(path, content)


def write_to_config(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "config.py"
    _write_to(path, content)


def write_to_init(output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "__init__.py"
    _write_to(path, "")


def flush_buffers() -> None:
    """Write all buffered content to files at once"""
    global _client_buffer, _schemas_buffer
    _client_buffer = []
    _schemas_buffer = []


def _write_to(
    path: pathlib.Path,
    content: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as f:
        f.write(content)


def flush_client_buffer(output_dir: str) -> None:
    """Write all buffered client content to client.py"""
    if _client_buffer:
        path = pathlib.Path(output_dir) / "client.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            f.write("".join(_client_buffer))
        _client_buffer.clear()


def flush_schemas_buffer(output_dir: str) -> None:
    """Write all buffered schema content to schemas.py"""
    if _schemas_buffer:
        path = pathlib.Path(output_dir) / "schemas.py"
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a") as f:
            f.write("".join(_schemas_buffer))
        _schemas_buffer.clear()
