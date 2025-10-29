import os
import os.path

import clientele.generators
import clientele.generators.basic.writer
import clientele.settings
import clientele.utils


class BasicGenerator(clientele.generators.Generator):
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
            ("config.py", "config_py.jinja2", clientele.generators.basic.writer.write_to_config),
            ("client.py", "client_py.jinja2", clientele.generators.basic.writer.write_to_client),
            ("http.py", "http_py.jinja2", clientele.generators.basic.writer.write_to_http),
            ("schemas.py", "schemas_py.jinja2", clientele.generators.basic.writer.write_to_schemas),
        )

    def generate(self) -> None:
        client_project_directory_path = clientele.utils.get_client_project_directory_path(output_dir=self.output_dir)
        if os.path.exists(f"{self.output_dir}/MANIFEST.md"):
            os.remove(f"{self.output_dir}/MANIFEST.md")
        manifest_template = clientele.generators.basic.writer.templates.get_template("manifest.jinja2")
        manifest_content = manifest_template.render(
            command=f"-o {self.output_dir}", clientele_version=clientele.settings.VERSION
        )
        clientele.generators.basic.writer.write_to_manifest(content=manifest_content + "\n", output_dir=self.output_dir)
        clientele.generators.basic.writer.write_to_init(output_dir=self.output_dir)
        for (
            client_file,
            client_template_file,
            write_func,
        ) in self.file_name_writer_tuple:
            if os.path.exists(f"{self.output_dir}/{client_file}"):
                os.remove(f"{self.output_dir}/{client_file}")
            template = clientele.generators.basic.writer.templates.get_template(client_template_file)
            content = template.render(
                client_project_directory_path=client_project_directory_path,
            )
            write_func(content, output_dir=self.output_dir)
