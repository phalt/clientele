# Publishing

How to publish new versions

## Regenerate test clients

This will mean the example clients always show the latest version in their MANIFEST.md files.

Update the `settings.py` file to make the version match the tag:

```python
# clientele/settings.py
VERSION = "<VERSION>"
```

Regenerate the test clients

```sh
make generate-test-clients
```

When you type `git diff` you should now see the test clients have updated their MANIFEST.md files.

## Update the package version

This updates the project to be a new version:

```toml
# pyproject.toml
version = "<VERSION>"
```

Now update the package:

```sh
make install
```

The `uv.lock` file should update to the new version.

## Commit all the changes together

Put all these changes into a single commit, then push to main:

```sh
git add .
git commit -m "version <VERSION>"
git push origin main
```

## Create a new tag

Make sure you are on the main branch and on the correct commit for releasing:

```sh
# Latest commit on main
git checkout main
git pull origin main
# Make sure you have the latest tags
git fetch --tags
# Check the list doesn't already have the tag you're creating
git tag
```

Create the new tag:

```sh
git tag <VERSION>
```

Push the tag to remote:

```sh
git push origin --tags
```

Go to https://github.com/phalt/clientele/tags and create a new release from the tag.

Copy and paste the correct version contents from CHANGELOG.md.

Mark as the latest release.

## Pubish documentation

Nice and easy

```sh
make deploy-docs
```

Takes about 5-10 minutes to deploy fully.

## Release to pypi

This requires pypi login details.

```sh
$UV_PUBLISH_TOKEN=<TOKEN> make release
```

## Release to homebrew

TODO
