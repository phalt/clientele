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

release:  ## Build a new version and release it
	uv build
	uv publish

mypy: ## Run a static syntax check
	uv run mypy .

format: ## Format the code correctly
	uv run ruff format .
	uv run ruff check --fix .

clean:  ## Clear any cache files and test files
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf test_output
	rm -rf site/
	rm -rf dist/
	rm -rf **/__pycache__
	rm -rf **/*.pyc

test:  ## Run tests
	uv run pytest -vvv

shell:  ## Run an ipython shell
	uv run ipython

generate-test-clients:  ## regenerate the test clients in the tests/ directory
	uv sync
	uv run clientele generate -f example_openapi_specs/best.json -o tests/test_client/ --regen t
	uv run clientele generate -f example_openapi_specs/best.json -o tests/async_test_client/ --asyncio t --regen t
	uv run clientele generate-class -f example_openapi_specs/best.json -o tests/test_class_client/ --regen t
	uv run clientele generate-class -f example_openapi_specs/best.json -o tests/async_test_class_client/ --asyncio t --regen t

brew-status:  ## Check the status of Homebrew publishing setup
	@homebrew/check_status.sh

brew-formula:  ## Generate Homebrew formula for current version
	uv run python homebrew/generate_formula.py

brew-verify:  ## Verify the generated Homebrew formula (requires Homebrew installed)
	@if command -v brew >/dev/null 2>&1; then \
		brew audit --strict --online homebrew/clientele.rb; \
	else \
		echo "Homebrew is not installed. Skipping verification."; \
	fi

brew-test-local:  ## Test installing the formula locally (requires Homebrew installed)
	@if command -v brew >/dev/null 2>&1; then \
		echo "Testing formula installation..."; \
		brew install --build-from-source homebrew/clientele.rb; \
		echo "Running version check..."; \
		clientele version; \
	else \
		echo "Error: Homebrew is not installed."; \
		exit 1; \
	fi
