# Server Examples

This directory contains working example server applications that demonstrate how to use Clientele with different Python web frameworks.

## Purpose

These examples serve as:

1. **Reference Implementations**: Real, working boilerplate applications that match the code examples in our framework-specific documentation
2. **Testing Ground**: Live servers you can run to test Clientele's client generation against actual APIs
3. **Learning Resources**: Practical examples showing best practices for each framework

## Available Examples

### FastAPI

Location: `fastapi/`

A minimal FastAPI application demonstrating:
- Basic endpoint setup
- OpenAPI schema generation
- Custom operation IDs for cleaner client function names

See [FastAPI documentation](../docs/framework-fastapi.md) for detailed usage.

### Django REST Framework

Location: `django-rest-framework/`

A Django application with DRF and drf-spectacular demonstrating:
- ViewSet-based API design
- OpenAPI schema generation via drf-spectacular
- Custom operation IDs with `@extend_schema`

See [Django REST Framework documentation](../docs/framework-drf.md) for detailed usage.

### Django Ninja

Location: `django-ninja/`

A Django application with Django Ninja demonstrating:
- Ninja API endpoint setup
- Pydantic schema integration
- OpenAPI schema generation

See [Django Ninja documentation](../docs/framework-django-ninja.md) for detailed usage.

## Usage

Each example directory contains:
- A working server application
- Instructions in its own README for running the server
- A `client/` directory (placeholder for generated clients)

To use an example:

1. Navigate to the framework directory (e.g., `cd fastapi/`)
2. Follow the setup instructions in that directory's README
3. Run the server
4. Generate a client using Clientele pointing at the running server
5. The generated client will go in the `client/` subdirectory

## Contributing

When contributing server examples:
- Keep them minimal and focused on demonstrating Clientele integration
- Match the code examples shown in the framework documentation
- Ensure they use standard boilerplate patterns for each framework
- Include clear setup and run instructions
