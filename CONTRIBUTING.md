# Contributing

First things first: thank you for contributing! This project will be succesful thanks to everyone who contributes, and we're happy to have you.

## Bug or issue?

To raise a bug or issue please use [our GitHub](https://github.com/phalt/clientele/issues).

Please check the issue has not be raised before by using the search feature.

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

Install all the dependencies:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
make install
```

To make sure you have things set up correctly, please run the tests:

```sh
make test
```

### Preparing changes for review

Once you have made changes, here is a good check list to run through to get it published for review:

Regenerate the test clients to see what has changed, and if tests pass:

```sh
make generate-test-clients
make test
```

Check your `git diff` to see if anything drastic has changed. If changes happen that you did not expect, something has gone wrong. We want to make sure the clients do not change drastically when adding new features unless it is intended.

Format and lint the code:

```sh
make format
```

Note that, the auto-generated black formatted code will be changed again because this project uses `ruff` for additional formatting. That's okay.

Make sure you add to `CHANGELOG.md` and `docs/CHANGELOG.md` what changes you have made.

Make sure you add your name to `CONTRIBUTORS.md` as well!

### Making a pull request

Please push your changes up to a feature branch and make a new [pull request](https://github.com/phalt/clientele/compare) on GitHub.

Please add a description to the PR and some information about why the change is being made.

After a review you might need to make more changes.

Once accepted, a core contributor will merge your changes!
