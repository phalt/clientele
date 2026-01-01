#!/usr/bin/env python3
"""
Regenerate server example clients using the framework generator.
"""

import sys
from pathlib import Path

# Add parent directory to path to import clientele
sys.path.insert(0, str(Path(__file__).parent.parent))

from clientele.cli import _load_openapi_spec
from clientele.generators.framework.generator import FrameworkGenerator


def regenerate_example(name: str, spec_file: str, output_dir: str):
    """Regenerate a single server example client."""
    print(f"\n{'='*60}")
    print(f"Regenerating {name}...")
    print(f"{'='*60}")
    
    # Load spec
    spec = _load_openapi_spec(file=spec_file)
    
    # Create generator
    generator = FrameworkGenerator(
        spec=spec,
        output_dir=output_dir,
        asyncio=False,  # Framework examples are sync
        regen=True,
        url=None,
        file=spec_file,
    )
    
    # Generate
    generator.generate()
    
    print(f"✓ Regenerated {name}")


def main():
    """Regenerate all server example clients."""
    base_dir = Path(__file__).parent.parent
    examples = [
        ("FastAPI", "server_examples/fastapi/openapi.json", "server_examples/fastapi/client"),
        ("Django REST Framework", "server_examples/django_rest_framework/openapi.yaml", "server_examples/django_rest_framework/client"),
        ("Django Ninja", "server_examples/django_ninja/openapi.json", "server_examples/django_ninja/client"),
    ]
    
    for name, spec_file, output_dir in examples:
        spec_path = str(base_dir / spec_file)
        output_path = str(base_dir / output_dir)
        regenerate_example(name, spec_path, output_path)
    
    print(f"\n{'='*60}")
    print("✓ All server examples regenerated successfully!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
