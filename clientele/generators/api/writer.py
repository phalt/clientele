import collections
import pathlib

import jinja2

templates = jinja2.Environment(loader=jinja2.PackageLoader("clientele", "generators/api/templates/"))

# Buffer for accumulating file content before writing
_file_buffers: dict[str, list[str]] = collections.defaultdict(list)


def write_to_schemas(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "schemas.py"
    _buffer_content(path, content)


def write_to_client(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "client.py"
    _buffer_content(path, content)


def write_to_manifest(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "MANIFEST.md"
    _write_to(path, content)


def write_to_config(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "config.py"
    _write_to(path, content)


def write_to_init(output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "__init__.py"
    _write_to(path, "")


def write_to_pyproject(content: str, output_dir: str) -> None:
    path = pathlib.Path(output_dir) / "pyproject.toml"
    _write_to(path, content)


def _buffer_content(path: pathlib.Path, content: str) -> None:
    """Buffer content to be written later in a single operation."""
    _file_buffers[str(path)].append(content)


def flush_buffers() -> None:
    """Write all buffered content to files in a single operation per file."""
    for path_str, contents in _file_buffers.items():
        path = pathlib.Path(path_str)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            f.write("".join(contents))
    _file_buffers.clear()


def _write_to(
    path: pathlib.Path,
    content: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(content)
