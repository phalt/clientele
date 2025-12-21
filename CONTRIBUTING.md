# Contributing

First things first: thank you for contributing! This project will be successful thanks to everyone who contributes, and we're happy to have you.

## Bug or issue?

To raise a bug or issue please use [our GitHub](https://github.com/phalt/clientele/issues).

Please check the issue has not been raised before by using the search feature.

When submitting an issue or bug, please make sure you provide thorough detail on:

1. The version of clientele you are using
2. Any errors or outputs you see in your terminal
3. The OpenAPI schema you are using (this is particularly important).

## Contribution

If you want to directly contribute you can do so in two ways:

1. Documentation
2. Code

### Documentation

We use [mkdocs](https://www.mkdocs.org/) and [GitHub pages](https://pages.github.com/) to deploy our docs.

Fixing grammar, spelling mistakes, or expanding the documentation to cover features that are not yet documented, are all valuable contributions.

Please see the **Set up** instructions below to run the docs locally on your computer.

### Code

Contribution by writing code for new features, or fixing bugs, is a great way to contribute to the project.

#### Set up

Clone the repo:

```sh
git@github.com:phalt/clientele.git
cd clientele
```

Move to a feature branch:

```sh
git branch -B my-branch-name
```

Install UV (if not already installed):

```sh
# On macOS and Linux:
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip:
pip install uv
```

Install all the dependencies:

```sh
make install
```

This will use UV to create a virtual environment and install all dependencies. UV handles the virtual environment automatically, so you don't need to manually activate it.

To make sure you have things set up correctly, please run the tests:

```sh
make test
```

You can also test clientele against all schemas from the APIs-guru/openapi-directory repository (4000+ schemas):

```sh
make test-openapi-directory
```

This command clones the openapi-directory, generates test clients for all schemas, and reports results. This is useful for ensuring clientele works with real-world OpenAPI schemas.

### Preparing changes for review

Once you've made changes, here's a good checklist to run through before publishing for review:

Regenerate the test clients to see what has changed, and if tests pass:

```sh
make generate-test-clients
make test
```

Check your `git diff` to see if anything drastic has changed. If unexpected changes appear, something has gone wrong. We want to make sure the clients don't change drastically when adding new features unless it's intended.

Format and lint the code:

```sh
make format
```

The generated code is automatically formatted with Ruff, which provides both code formatting and linting fixes.

Make sure you add to `CHANGELOG.md` and `docs/CHANGELOG.md` what changes you have made.

Make sure you add your name to `CONTRIBUTORS.md` as well!

### Making a pull request

Please push your changes up to a feature branch and make a new [pull request](https://github.com/phalt/clientele/compare) on GitHub.

Please add a description to the PR and some information about why the change is being made.

After a review, you might need to make more changes.

Once accepted, a core contributor will merge your changes!
