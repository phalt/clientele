import os


def get_client_project_directory_path(output_dir: str) -> str:
    """
    Returns a dot-notation path for the client directory.
    Assumes that the `clientele` command is being run in the
    project root directory.

    For absolute paths, returns an empty string (which will result in
    relative imports being used).
    """
    # If it's an absolute path, return empty string for relative imports
    if os.path.isabs(output_dir):
        return ""

    # Normalize the path and convert to Python module notation
    # Strip trailing slashes first
    normalized_path = output_dir.rstrip(os.sep)

    # Split by path separator and join with dots
    parts = normalized_path.split(os.sep)

    # Filter out empty parts
    parts = [p for p in parts if p]

    # Return the full path as a Python module path
    if parts:
        return ".".join(parts)

    return ""
