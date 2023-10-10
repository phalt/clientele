import os


def get_client_project_directory_path(output_dir: str) -> str:
    """
    Returns a dot-notation path for the client directory.
    Assumes that the `clientele` command is being run in the
    project root directory.
    """
    return ".".join(os.path.join(output_dir).split("/")[:-1])
