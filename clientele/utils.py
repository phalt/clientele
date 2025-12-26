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

    # Check if path has trailing slash
    has_trailing_slash = output_dir.endswith(os.sep)

    # Split the path by separator
    parts = output_dir.split(os.sep)

    # Filter out empty parts
    parts = [p for p in parts if p]

    # If no trailing slash, remove the last component (the directory name)
    # If trailing slash, include all components
    if not has_trailing_slash and len(parts) > 1:
        parts = parts[:-1]
    elif not has_trailing_slash and len(parts) == 1:
        # Single directory with no trailing slash means no parent
        return ""

    # Return the path as a Python module path
    if parts:
        return ".".join(parts)

    return ""
