from pathlib import Path


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


def _write_to(
    path: Path,
    content: str,
) -> None:
    with path.open("a") as f:
        f.write(content)
