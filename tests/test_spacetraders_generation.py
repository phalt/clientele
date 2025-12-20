"""Tests for generating client from spacetraders OpenAPI spec."""

import tempfile
from pathlib import Path

from click.testing import CliRunner

from clientele import cli


def test_generate_spacetraders_client():
    """Test that spacetraders client can be generated without errors."""
    runner = CliRunner()
    
    spec_path = Path(__file__).parent / "fixtures" / "realworld" / "spacetraders.yaml"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "spacetraders_client"
        
        result = runner.invoke(
            cli.cli_group,
            ["generate", "--file", str(spec_path), "--output", str(output_dir), "--regen", "true"],
        )
        
        # Should succeed
        assert result.exit_code == 0, f"Generation failed with: {result.output}"
        assert "Client generated" in result.output or "generated" in result.output.lower()
        
        # Check that files were created
        assert output_dir.exists()
        client_file = output_dir / "client.py"
        schemas_file = output_dir / "schemas.py"
        assert client_file.exists(), "client.py was not created"
        assert schemas_file.exists(), "schemas.py was not created"
        
        # Read the generated client.py
        client_content = client_file.read_text()
        
        # Test Issue 1: Path parameters should use snake_case variable names in URLs
        # The get_faction function should use {faction_symbol} not {factionSymbol}
        assert "def get_faction(faction_symbol: str)" in client_content, \
            "get_faction function should have faction_symbol parameter"
        assert 'url=f"/factions/{faction_symbol}"' in client_content, \
            "get_faction should use {faction_symbol} in URL, not {factionSymbol}"
        
        # Read the generated schemas.py
        schemas_content = schemas_file.read_text()
        
        # Test Issue 2: Schema classes should not have duplicate ApplicationJson names
        # Count occurrences of "class ApplicationJson"
        application_json_count = schemas_content.count("class ApplicationJson(")
        assert application_json_count == 0, \
            f"Found {application_json_count} duplicate 'ApplicationJson' classes. Each should have unique names."
        
        # Test Issue 3: Schema types should not have weird encoded paths
        # These weird references should be replaced with typing.Any
        weird_ref_patterns = [
            "#Paths~1",
            "%7B",  # URL-encoded {
            "%7D",  # URL-encoded }
        ]
        for pattern in weird_ref_patterns:
            assert pattern not in schemas_content, \
                f"Found encoded path reference '{pattern}' in schemas. Should use typing.Any instead."


def test_generate_spacetraders_client_python_validity():
    """Test that generated spacetraders client is valid Python that can be imported."""
    import importlib.util
    import sys
    
    runner = CliRunner()
    spec_path = Path(__file__).parent / "fixtures" / "realworld" / "spacetraders.yaml"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir) / "spacetraders_client"
        
        result = runner.invoke(
            cli.cli_group,
            ["generate", "--file", str(spec_path), "--output", str(output_dir), "--regen", "true"],
        )
        
        assert result.exit_code == 0
        
        # Try to import the generated schemas module
        schemas_file = output_dir / "schemas.py"
        spec = importlib.util.spec_from_file_location("spacetraders_schemas", schemas_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules["spacetraders_schemas"] = module
            try:
                spec.loader.exec_module(module)
            except Exception as e:
                # Clean up
                if "spacetraders_schemas" in sys.modules:
                    del sys.modules["spacetraders_schemas"]
                raise AssertionError(f"Generated schemas.py is not valid Python: {e}")
            finally:
                # Clean up
                if "spacetraders_schemas" in sys.modules:
                    del sys.modules["spacetraders_schemas"]
