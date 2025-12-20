"""
Test for complex schemas with oneOf, anyOf, and nullable support
"""

import subprocess
import sys
from pathlib import Path

import pytest


def test_complex_schemas_generation(tmp_path):
    """Test that complex schemas with oneOf, anyOf, and nullable are properly generated"""
    output_dir = tmp_path / "complex_client"
    output_dir.mkdir()

    # Get absolute path to the spec file
    spec_file = Path(__file__).parent.parent / "example_openapi_specs" / "complex_schemas.json"
    assert spec_file.exists(), f"Spec file not found: {spec_file}"

    # Generate client from the complex schemas spec
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "clientele.cli",
            "generate",
            "-f",
            str(spec_file),
            "-o",
            str(output_dir),
            "--regen",
            "t",
        ],
        capture_output=True,
        text=True,
    )
    
    # Print output for debugging
    print(f"returncode: {result.returncode}")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    print(f"Output dir exists: {output_dir.exists()}")
    if output_dir.exists():
        print(f"Output directory contents: {list(output_dir.iterdir())}")
    
    assert result.returncode == 0, f"Generation failed: stdout={result.stdout}\nstderr={result.stderr}"

    # Read the generated schemas file
    schemas_file = output_dir / "schemas.py"
    assert schemas_file.exists(), f"schemas.py not found. Directory contents: {list(output_dir.iterdir())}"

    content = schemas_file.read_text()

    # Check that oneOf creates type aliases
    assert 'PetRequest = "Cat" | "Dog"' in content
    assert 'PaymentMethodRequest = "CreditCard" | "BankTransfer" | "PayPal"' in content

    # Check that anyOf creates union types in properties
    assert "id: str | int" in content

    # Check that nullable creates Optional types
    assert "optional_nullable_field: typing.Optional[str]" in content
    assert "nullable_number: typing.Optional[int]" in content

    # Check that individual schemas are still created
    assert "class Cat(pydantic.BaseModel):" in content
    assert "class Dog(pydantic.BaseModel):" in content
    assert "class CreditCard(pydantic.BaseModel):" in content
    assert "class BankTransfer(pydantic.BaseModel):" in content
    assert "class PayPal(pydantic.BaseModel):" in content


def test_complex_schemas_class_generation(tmp_path):
    """Test that complex schemas work with class-based client generation"""
    output_dir = tmp_path / "complex_class_client"
    output_dir.mkdir()

    # Get absolute path to the spec file
    spec_file = Path(__file__).parent.parent / "example_openapi_specs" / "complex_schemas.json"
    assert spec_file.exists(), f"Spec file not found: {spec_file}"

    # Generate class-based client from the complex schemas spec
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "clientele.cli",
            "generate-class",
            "-f",
            str(spec_file),
            "-o",
            str(output_dir),
            "--regen",
            "t",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"Generation failed: {result.stderr}"

    # Read the generated schemas file
    schemas_file = output_dir / "schemas.py"
    assert schemas_file.exists()

    content = schemas_file.read_text()

    # Same checks as function-based
    assert 'PetRequest = "Cat" | "Dog"' in content
    assert 'PaymentMethodRequest = "CreditCard" | "BankTransfer" | "PayPal"' in content
    assert "id: str | int" in content
    assert "optional_nullable_field: typing.Optional[str]" in content


def test_validation_error_anyof():
    """Test that ValidationError from best.json properly handles anyOf"""
    from tests.test_client import schemas

    # Get the ValidationError class
    validation_error = schemas.ValidationError

    # Check that it has the correct fields
    assert hasattr(validation_error, "__annotations__")
    assert "loc" in validation_error.__annotations__

    # The annotation is a string due to from __future__ import annotations
    # Let's check the string representation
    loc_annotation_str = str(validation_error.__annotations__["loc"])
    
    # Should contain list and union of str | int
    assert "list" in loc_annotation_str
    assert "str" in loc_annotation_str
    assert "int" in loc_annotation_str
    
    # Or check the model fields which are evaluated
    loc_field = validation_error.model_fields["loc"]
    assert loc_field.annotation is not None

