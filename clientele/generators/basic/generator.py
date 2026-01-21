import os
import pathlib

from clientele import generators, settings, utils
from clientele.generators.basic import writer


class BasicGenerator(generators.Generator):
    """
    Generates a "basic" HTTP client, which is just a file structure
    and some useful imports.

    This generator can be used as a template for future generators.

    It is also a great way to generate a file structure for consistent HTTP API clients
    that are not OpenAPI but you want to keep the same file structure.
    """

    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir

        self.file_name_writer_tuple = (
            ("config.py", "config_py.jinja2", writer.write_to_config),
            ("client.py", "client_py.jinja2", writer.write_to_client),
            ("schemas.py", "schemas_py.jinja2", writer.write_to_schemas),
        )

    def generate(self) -> None:
        client_project_directory_path = utils.get_client_project_directory_path(output_dir=self.output_dir)
        manifest_file = pathlib.Path(self.output_dir) / "MANIFEST.md"
        if manifest_file.exists():
            os.remove(manifest_file)
        manifest_template = writer.templates.get_template("manifest.jinja2")
        manifest_content = manifest_template.render(command=f"-o {self.output_dir}", clientele_version=settings.VERSION)
        writer.write_to_manifest(content=manifest_content + "\n", output_dir=self.output_dir)
        writer.write_to_init(output_dir=self.output_dir)
        for (
            client_file,
            client_template_file,
            write_func,
        ) in self.file_name_writer_tuple:
            file_path = pathlib.Path(self.output_dir) / client_file
            if file_path.exists():
                os.remove(file_path)
            template = writer.templates.get_template(client_template_file)
            content = template.render(
                client_project_directory_path=client_project_directory_path,
            )
            write_func(content, output_dir=self.output_dir)
