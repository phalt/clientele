def write_to_response(content: str, output_dir: str) -> None:
    _write_to(f"{output_dir}schemas.py", content)


def write_to_client(content: str, output_dir: str) -> None:
    _write_to(f"{output_dir}client.py", content)


def _write_to(
    path: str,
    content: str,
) -> None:
    with open(path, "a") as f:
        f.write(content)
