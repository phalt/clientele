help:
	@echo Developer commands for PopenAPI
	@echo
	@grep -E '^[ .a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo

install:  ## Install requirements ready for development
	poetry install

mypy: ## Run a static syntax check
	poetry run mypy src/ cli.py

lint: ## Format the code correctly
	poetry run black .
	poetry run ruff --fix .

clean:  ## Clear any cache files and test files
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf test_output

shell:  ## Run an ipython shell
	poetry run ipython
