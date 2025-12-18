"""Tests for standard generator writer functions."""

import tempfile
from pathlib import Path

from clientele.generators.standard import writer


def test_write_to_schemas():
    """Test writing content to schemas.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test schema content\nclass TestSchema:\n    pass\n"
        writer.write_to_schemas(content, tmpdir)
        writer.flush_buffers()

        schema_file = Path(tmpdir) / "schemas.py"
        assert schema_file.exists()
        assert content in schema_file.read_text()


def test_write_to_http():
    """Test writing content to http.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test HTTP content\ndef make_request():\n    pass\n"
        writer.write_to_http(content, tmpdir)
        writer.flush_buffers()

        http_file = Path(tmpdir) / "http.py"
        assert http_file.exists()
        assert content in http_file.read_text()


def test_write_to_client():
    """Test writing content to client.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test client content\ndef my_api_call():\n    pass\n"
        writer.write_to_client(content, tmpdir)
        writer.flush_buffers()

        client_file = Path(tmpdir) / "client.py"
        assert client_file.exists()
        assert content in client_file.read_text()


def test_write_to_manifest():
    """Test writing content to MANIFEST.md file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# API Manifest\n\nThis is a test manifest.\n"
        writer.write_to_manifest(content, tmpdir)

        manifest_file = Path(tmpdir) / "MANIFEST.md"
        assert manifest_file.exists()
        assert manifest_file.read_text() == content


def test_write_to_config():
    """Test writing content to config.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "API_BASE_URL = 'https://api.example.com'\n"
        writer.write_to_config(content, tmpdir)

        config_file = Path(tmpdir) / "config.py"
        assert config_file.exists()
        assert config_file.read_text() == content


def test_write_to_init():
    """Test writing empty __init__.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_init(tmpdir)

        init_file = Path(tmpdir) / "__init__.py"
        assert init_file.exists()
        assert init_file.read_text() == ""


def test_flush_buffers_writes_multiple_files():
    """Test that flush_buffers writes all buffered content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Buffer multiple writes to different files
        writer.write_to_schemas("# Schema 1\n", tmpdir)
        writer.write_to_schemas("# Schema 2\n", tmpdir)
        writer.write_to_client("# Client code\n", tmpdir)
        writer.write_to_http("# HTTP code\n", tmpdir)

        # Files shouldn't exist yet
        assert not (Path(tmpdir) / "schemas.py").exists()
        assert not (Path(tmpdir) / "client.py").exists()

        # Flush all buffers
        writer.flush_buffers()

        # Now files should exist with combined content
        schema_file = Path(tmpdir) / "schemas.py"
        assert schema_file.exists()
        content = schema_file.read_text()
        assert "# Schema 1\n" in content
        assert "# Schema 2\n" in content

        client_file = Path(tmpdir) / "client.py"
        assert client_file.exists()
        assert "# Client code\n" in client_file.read_text()


def test_flush_buffers_clears_buffer():
    """Test that flush_buffers clears the buffer after writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_schemas("# Test\n", tmpdir)
        writer.flush_buffers()

        # Buffer should be cleared, so flushing again shouldn't write anything
        schema_file = Path(tmpdir) / "schemas.py"
        original_content = schema_file.read_text()

        writer.flush_buffers()

        # Content should be unchanged
        assert schema_file.read_text() == original_content


def test_buffer_content_accumulates():
    """Test that multiple writes to same file accumulate in buffer."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_schemas("Part 1\n", tmpdir)
        writer.write_to_schemas("Part 2\n", tmpdir)
        writer.write_to_schemas("Part 3\n", tmpdir)
        writer.flush_buffers()

        schema_file = Path(tmpdir) / "schemas.py"
        content = schema_file.read_text()
        assert content == "Part 1\nPart 2\nPart 3\n"


def test_write_creates_parent_directories():
    """Test that writer creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "subdir" / "nested"
        writer.write_to_config("# Config\n", str(nested_dir))

        config_file = nested_dir / "config.py"
        assert config_file.exists()
        assert config_file.read_text() == "# Config\n"
