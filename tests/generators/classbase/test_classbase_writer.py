"""Tests for classbase generator writer functions."""

import tempfile
from pathlib import Path

from clientele.generators.classbase import writer


def test_write_to_schemas():
    """Test writing content to schemas.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test schema content\nclass TestSchema:\n    pass\n"
        writer.write_to_schemas(content, tmpdir)

        schema_file = Path(tmpdir) / "schemas.py"
        assert schema_file.exists()
        assert content in schema_file.read_text()


def test_write_to_http():
    """Test writing content to http.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test HTTP content\ndef make_request():\n    pass\n"
        writer.write_to_http(content, tmpdir)

        http_file = Path(tmpdir) / "http.py"
        assert http_file.exists()
        assert content in http_file.read_text()


def test_write_to_client_buffers_content():
    """Test that write_to_client buffers content instead of writing immediately."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# Test client content\ndef my_api_call():\n    pass\n"
        writer.write_to_client(content, tmpdir)

        # File shouldn't exist yet because content is buffered
        client_file = Path(tmpdir) / "client.py"
        assert not client_file.exists()

        # Flush the buffer to write the file
        writer.flush_client_buffer(tmpdir)
        assert client_file.exists()
        assert content in client_file.read_text()


def test_write_to_manifest():
    """Test writing content to MANIFEST.md file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "# API Manifest\n\nThis is a test manifest.\n"
        writer.write_to_manifest(content, tmpdir)

        manifest_file = Path(tmpdir) / "MANIFEST.md"
        assert manifest_file.exists()
        assert content in manifest_file.read_text()


def test_write_to_config():
    """Test writing content to config.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        content = "API_BASE_URL = 'https://api.example.com'\n"
        writer.write_to_config(content, tmpdir)

        config_file = Path(tmpdir) / "config.py"
        assert config_file.exists()
        assert content in config_file.read_text()


def test_write_to_init():
    """Test writing empty __init__.py file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_init(tmpdir)

        init_file = Path(tmpdir) / "__init__.py"
        assert init_file.exists()
        assert init_file.read_text() == ""


def test_flush_client_buffer_writes_buffered_content():
    """Test that flush_client_buffer writes all buffered client content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Buffer multiple writes
        writer.write_to_client("# Part 1\n", tmpdir)
        writer.write_to_client("# Part 2\n", tmpdir)
        writer.write_to_client("# Part 3\n", tmpdir)

        # File shouldn't exist yet
        client_file = Path(tmpdir) / "client.py"
        assert not client_file.exists()

        # Flush the buffer
        writer.flush_client_buffer(tmpdir)

        # Now file should exist with all content
        assert client_file.exists()
        content = client_file.read_text()
        assert "# Part 1\n" in content
        assert "# Part 2\n" in content
        assert "# Part 3\n" in content


def test_flush_client_buffer_clears_buffer():
    """Test that flush_client_buffer clears the buffer after writing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_client("# Test\n", tmpdir)
        writer.flush_client_buffer(tmpdir)

        client_file = Path(tmpdir) / "client.py"
        original_content = client_file.read_text()

        # Flush again - should not write anything new
        writer.flush_client_buffer(tmpdir)

        # Content should be unchanged
        assert client_file.read_text() == original_content


def test_flush_buffers_clears_all_buffers():
    """Test that flush_buffers clears all buffer lists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer.write_to_client("# Client\n", tmpdir)

        # Call flush_buffers (which clears but doesn't write)
        writer.flush_buffers()

        # Now flush_client_buffer should not write anything
        writer.flush_client_buffer(tmpdir)

        client_file = Path(tmpdir) / "client.py"
        assert not client_file.exists()


def test_write_appends_to_existing_files():
    """Test that writes append to existing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write initial content
        writer.write_to_http("# Part 1\n", tmpdir)

        # Write more content to the same file
        writer.write_to_http("# Part 2\n", tmpdir)

        http_file = Path(tmpdir) / "http.py"
        content = http_file.read_text()
        assert "# Part 1\n" in content
        assert "# Part 2\n" in content


def test_write_creates_parent_directories():
    """Test that writer creates parent directories if they don't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        nested_dir = Path(tmpdir) / "subdir" / "nested"
        writer.write_to_config("# Config\n", str(nested_dir))

        config_file = nested_dir / "config.py"
        assert config_file.exists()
        assert "# Config\n" in config_file.read_text()


def test_flush_client_buffer_with_empty_buffer():
    """Test that flush_client_buffer handles empty buffer gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Don't write anything, just flush
        writer.flush_client_buffer(tmpdir)

        # File should not be created
        client_file = Path(tmpdir) / "client.py"
        assert not client_file.exists()


def test_flush_schemas_buffer_with_content():
    """Test flush_schemas_buffer writes buffered schema content."""
    import tempfile
    from pathlib import Path

    from clientele.generators.classbase import writer

    with tempfile.TemporaryDirectory() as tmpdir:
        # First, we need to buffer some schema content
        # The _schemas_buffer is a module-level variable, so we need to add to it directly
        writer._schemas_buffer.append("# Schema content\n")
        writer._schemas_buffer.append("class TestSchema:\n")
        writer._schemas_buffer.append("    pass\n")

        # Now flush it
        writer.flush_schemas_buffer(tmpdir)

        # Check that the file was created
        schema_file = Path(tmpdir) / "schemas.py"
        assert schema_file.exists()

        content = schema_file.read_text()
        assert "# Schema content" in content
        assert "class TestSchema" in content

        # Buffer should be cleared
        assert len(writer._schemas_buffer) == 0


def test_flush_schemas_buffer_with_empty_buffer():
    """Test flush_schemas_buffer does nothing when buffer is empty."""
    import tempfile
    from pathlib import Path

    from clientele.generators.classbase import writer

    with tempfile.TemporaryDirectory() as tmpdir:
        # Make sure buffer is empty
        writer._schemas_buffer.clear()

        # Flush empty buffer
        writer.flush_schemas_buffer(tmpdir)

        # File should not be created
        schema_file = Path(tmpdir) / "schemas.py"
        assert not schema_file.exists()
