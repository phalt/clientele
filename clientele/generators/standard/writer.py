from pathlib import Path

from jinja2 import Environment, PackageLoader

templates = Environment(loader=PackageLoader("clientele", "generators/standard/templates/"))


def write_to_schemas(content: str, output_dir: str) -> None:
    path = Path(output_dir) / "schemas.py"
    _write_to(path, content)


def write_to_http(content: str, output_dir: str) -> None:
    path = Path(output_dir) / "http.py"
    _write_to(path, content)


def write_to_client(content: str, output_dir: str) -> None:
    path = Path(output_dir) / "client.py"
    _write_to(path, content)


def write_to_manifest(content: str, output_dir: str) -> None:
    path = Path(output_dir) / "MANIFEST.md"
    _write_to(path, content)


def write_to_config(content: str, output_dir: str) -> None:
    path = Path(output_dir) / "config.py"
    _write_to(path, content)


def write_to_init(output_dir: str) -> None:
    path = Path(output_dir) / "__init__.py"
    _write_to(path, "")


def _write_to(
    path: Path,
    content: str,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as f:
        f.write(content)
