# Release checklist

Lodestone versions follow [PEP 440](https://packaging.python.org/en/latest/specifications/pep-0440/)
in package metadata and [semver](https://semver.org/) for public surfaces
after the first `0.1.0` release. See [compatibility.md](compatibility.md).

This candidate is **`0.1.0rc1`**. The annotated git tag is **`v0.1.0-rc1`**.
Do not tag `v0.1.0` and do not publish to PyPI from this checklist.

## Versioning

| Place | Form | Example |
|---|---|---|
| `src/lodestone/__init__.py` `__version__` | PEP 440 | `0.1.0rc1` |
| Wheel / PyPI name | PEP 440 | `lodestone_kb-0.1.0rc1-py3-none-any.whl` |
| Git tag | `v` + PEP 440 with a hyphen before `rc` | `v0.1.0-rc1` |
| CLI | `lodestone --version` | `0.1.0rc1` |

Hatch reads the version from `__version__`. After `0.1.0`, breaking changes
bump major (or the JSON schema suffix). Deprecations warn for one minor
version before removal.

## Cut a release candidate (already used for 0.1.0rc1)

1. All Must requirements green; evidence in `docs/evidence/<feature>.md`.
2. `CHANGELOG.md` section matches what actually shipped.
3. `openspec validate --all --strict` passes.
4. Merge to `main` with `git merge --no-ff` after green PR CI (including
   macOS). Archive the OpenSpec change as a direct commit on `main`.
5. Wait for green push CI on that `main` commit, including macOS.
6. Create an annotated tag on that commit:

```sh
git tag -a v0.1.0-rc1 -m "Lodestone 0.1.0rc1"
git push origin v0.1.0-rc1
```

The tag workflow (`.github/workflows/release.yml`) builds wheel + sdist,
uploads artifacts, and opens a **draft** GitHub Release. It does **not**
publish to PyPI.

## Later: cut `v0.1.0` to PyPI (maintainer, not this candidate)

1. Set `__version__` to `0.1.0` and add a `CHANGELOG.md` `0.1.0` section.
2. Merge, wait for green `main` CI including macOS.
3. Tag `v0.1.0` (annotated) and push the tag.
4. Download the wheel and sdist from the draft GitHub Release.
5. Publish with a trusted maintainer credential, for example:

```sh
python -m build
twine upload dist/*
```

or Trusted Publishing from a dedicated workflow that does not exist in
this tree yet. Add that workflow only when a maintainer is ready to
publish. Never put PyPI tokens in git.

## Verify a candidate locally

```sh
lodestone --version
python -m build
pip install dist/lodestone_kb-0.1.0rc1-py3-none-any.whl
lodestone --version
docker build -t lodestone-mcp:0.1.0rc1 .
```
