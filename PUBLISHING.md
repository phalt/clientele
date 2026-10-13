---
title: Release clientele
description: Release a new version of clientele to GitHub, the docs site and PyPI.
output_path: logs/release-<VERSION>.md
inputs:
  - name: VERSION
    description: The version to release, e.g. 2.3.2
    pattern: '^\d+\.\d+\.\d+$'
  - name: UV_PUBLISH_TOKEN
    description: PyPI API token for clientele
    secret: true
---

# ⚜️ Releasing clientele

clientele is released with this [paulrun](https://github.com/phalt/paulrun)
runbook:

```sh
uv tool install paulrun
paulrun check PUBLISHING.md
paulrun go PUBLISHING.md --dry
paulrun go PUBLISHING.md
```

You can also follow it by hand: each step's commands are in the order they run.

Before you start, make sure `CHANGELOG.md` has a section for the release,
headed `## <version>` or `## <version> UNRELEASED`, and that
`docs/CHANGELOG.md` is an exact copy of it. The changelog can be committed
already, or left uncommitted to go in with the version bump.

Each run is recorded in `logs/release-<version>.md`, which git ignores.

## Check before releasing

Releases are made from an up-to-date `main`, with nothing left uncommitted
except the changelog, for a version that hasn't been released yet.

```sh run
git switch main
git pull origin main
git fetch --tags

if [ -n "$(git status --porcelain -- . ':!CHANGELOG.md' ':!docs/CHANGELOG.md')" ]; then
  echo "Commit or stash these changes first:"
  git status --short
  exit 1
fi
if git rev-parse --quiet --verify "refs/tags/<VERSION>" > /dev/null; then
  echo "Tag <VERSION> already exists"
  exit 1
fi
if ! grep -qxF -e "## <VERSION>" -e "## <VERSION> UNRELEASED" CHANGELOG.md; then
  echo "CHANGELOG.md has no '## <VERSION>' section"
  exit 1
fi
if ! cmp -s CHANGELOG.md docs/CHANGELOG.md; then
  echo "docs/CHANGELOG.md doesn't match CHANGELOG.md. Copy it over:"
  echo "  cp CHANGELOG.md docs/CHANGELOG.md"
  exit 1
fi
```

## Run the checks

The same checks CI runs, before anything changes.

```sh run
uv run ruff format --check .
uv run ruff check .
make ty
make test
```

## Update the version

`pyproject.toml` holds clientele's only copy of its version. `uv version`
sets it and updates `uv.lock` to match. `clientele/settings.py` reads it from
the installed package, so `clientele version` and every generated client show
the new one.

```sh run
uv version <VERSION>
uv run clientele version
```

## Update the docs

`docs/install.md` shows what `clientele version` prints. `SECURITY.md` lists
the new version as the only supported one. The changelog's `UNRELEASED`
heading, if it has one, becomes just the version.

```python run
import os
import re
from pathlib import Path

version = os.environ["VERSION"]

install = Path("docs/install.md")
text, count = re.subn(r"^clientele \d+\.\d+\.\d+$", f"clientele {version}", install.read_text(), flags=re.MULTILINE)
if count != 1:
    raise SystemExit(f"Expected one 'clientele <version>' line in {install}, found {count}")
install.write_text(text)

# The supported version becomes "<version> or less" in the unsupported row.
security = Path("SECURITY.md")
text = security.read_text()
rows = re.search(
    r"^\| (\S+) +\| :white_check_mark: \|\n\| .+ or less +\| :x: +\|$",
    text,
    re.MULTILINE,
)
if rows is None:
    raise SystemExit(f"Couldn't find the supported versions table in {security}")
previous = rows.group(1)
if previous != version:
    new_rows = f"| {version:<13} | :white_check_mark: |\n| {previous + ' or less':<13} | :x:                |"
    security.write_text(text[: rows.start()] + new_rows + text[rows.end() :])

for changelog in [Path("CHANGELOG.md"), Path("docs/CHANGELOG.md")]:
    heading = rf"^## {re.escape(version)} UNRELEASED$"
    changelog.write_text(re.sub(heading, f"## {version}", changelog.read_text(), flags=re.MULTILINE))
```

## Regenerate the test clients

The example clients show the version in their `MANIFEST.md` files, so they're
regenerated with the new one.

```sh run
make generate-test-clients
git status --short
```

```confirm
Check the changes above. For <VERSION>, only these should have changed:

- pyproject.toml and uv.lock
- SECURITY.md, docs/install.md and the two CHANGELOG.md files
- the test clients' MANIFEST.md files

Anything else means the test clients were out of date. Stop here, and commit
those separately first.
```

## Commit and push

There's nothing to commit when rerunning a release that failed after this
step.

```sh run
git add -A
if git diff --cached --quiet; then
  echo "Nothing to commit"
else
  git commit -m "version <VERSION>"
fi
git push origin main
```

## Tag the release

```sh run
git tag <VERSION>
git push origin <VERSION>
```

## Create the GitHub release

These are the release notes, from `CHANGELOG.md`:

```python run
import os
import re
from pathlib import Path

version = re.escape(os.environ["VERSION"])
changelog = Path("CHANGELOG.md").read_text()
notes = re.search(rf"^## {version}\n(.*?)(?=^## |\Z)", changelog, re.MULTILINE | re.DOTALL)
print(notes.group(1).strip())
```

```confirm
Create a release on GitHub from tag <VERSION>:
https://github.com/phalt/clientele/releases/new?tag=<VERSION>

Title it <VERSION>, paste in the release notes above, and mark it as the
latest release.
```

## Publish the documentation

Takes about 5-10 minutes to deploy fully.

```sh run
make deploy-docs
```

## Release to PyPI

`uv publish` uploads everything in `dist/`, so clear it out first.

```sh run
rm -rf dist
# uv publish reads the token from $UV_PUBLISH_TOKEN.
make release
```
