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

    # Use the original logic but handle path separators properly
    # os.path.join with a single argument just returns the path
    parts = os.path.join(output_dir).split("/")

    # Remove the last component (empty string for trailing slash, or directory name)
    if len(parts) > 1:
        return ".".join(parts[:-1])

    return ""
