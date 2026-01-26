help:
	@echo Developer commands for Clientele
	@echo
	@grep -E '^[ .a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo

install:  ## Install requirements ready for development
	uv sync

deploy-docs:  ## Build and deploy the documentation
	uv run mkdocs build
	uv run mkdocs gh-deploy

docs-serve:  ## Run a local documentation server
	uv run mkdocs serve

release:  ## Build a new version and release it
	uv build
	uv publish

ty: ## Run a static syntax check
	uv run ty check .

format: ## Format the code correctly
	uv run ruff format .
	uv run ruff check --fix .

clean:  ## Clear any cache files and test files
	rm -rf .ty_cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf test_output
	rm -rf site/
	rm -rf dist/
	rm -rf **/__pycache__
	rm -rf **/*.pyc
	rm -rf htmlcov/
	rm -rf .coverage

test:  ## Run tests
	uv run pytest -vvv -x --cov=clientele --cov-report=term-missing --cov-report=html --cov-config=pyproject.toml

shell:  ## Run an ipython shell
	uv run ipython

generate-test-clients:  ## regenerate the test clients in the tests/ directory
	uv sync
	uv run clientele start-api -f example_openapi_specs/best.json -o tests/api_clients/test_client/ --regen
	uv run clientele start-api -o tests/api_clients/test_basic_client/ --regen
	uv run clientele start-api -f example_openapi_specs/best.json -o tests/api_clients/async_test_client/ --asyncio --regen
	uv run clientele start-api -f server_examples/fastapi/openapi.json -o server_examples/fastapi/client/ --regen
	uv run clientele start-api -f server_examples/django_rest_framework/openapi.yaml -o server_examples/django_rest_framework/client/ --regen
	uv run clientele start-api -f server_examples/django_ninja/openapi.json -o server_examples/django_ninja/client/ --regen

open-coverage-report:  ## Open the coverage report in a browser
	uv run python3 -m webbrowser file://$(PWD)/htmlcov/index.html
