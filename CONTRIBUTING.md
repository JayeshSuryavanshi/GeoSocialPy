# Contributing to GeoSocialX

Thanks for your interest in improving GeoSocialX. This is a small, standard-library-first Python package for the geospatial analysis of geotagged social and location data, and contributions of all sizes are welcome: bug reports, documentation fixes, new tests, and new features.

This guide covers how to set up a development environment, run the checks that CI enforces, and open a pull request that lands smoothly. It is written for the actual layout of this repository (`import geosocialx`, PyPI name `geosocialx`, `pip install geosocialx`).

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [Reporting bugs and requesting features](#reporting-bugs-and-requesting-features)
- [Development setup](#development-setup)
- [Running the checks](#running-the-checks)
- [Design principles](#design-principles)
- [Pull request workflow](#pull-request-workflow)
- [Coding conventions](#coding-conventions)
- [Documentation](#documentation)
- [Reporting a security issue](#reporting-a-security-issue)
- [Releases](#releases)
- [Recognition and licensing](#recognition-and-licensing)

## Ways to contribute

You do not need to write code to help:

- File a clear bug report or feature request on the [issue tracker](https://github.com/JayeshSuryavanshi/GeoSocialX/issues).
- Improve the README, docstrings, or the worked examples in `examples/`.
- Add or tighten tests, especially around edge cases in coordinate parsing and coverage accounting.
- Fix a bug or implement a feature (please open an issue first for anything non-trivial, so we can agree on the approach before you invest time).

## Reporting bugs and requesting features

Please open an issue at https://github.com/JayeshSuryavanshi/GeoSocialX/issues. There are no formal issue templates yet, so a good report simply includes:

- What you expected to happen and what actually happened.
- A minimal, self-contained snippet that reproduces the problem (ideally using `load_sample("sf")` or a tiny inline list of records, so no network or private data is needed).
- Your Python version and GeoSocialX version (`python -c "import geosocialx; print(geosocialx.__version__)"`).
- The full traceback, if there is one.

For feature requests, describe the use case first (what geospatial or coverage question you are trying to answer). That helps us keep new functionality aligned with the package's scope.

## Development setup

You will need Python 3.10 or newer (CI tests 3.10, 3.11, 3.12, and 3.13).

1. Fork the repository on GitHub, then clone your fork:

   ```bash
   git clone https://github.com/<your-username>/GeoSocialX.git
   cd GeoSocialX
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # on Windows: .venv\Scripts\activate
   ```

3. Install the package in editable mode with the extras you need. The `test` extra is the minimum for running the suite:

   ```bash
   pip install -e ".[test]"
   ```

   To work on the optional layers as well (interactive maps, the `.env`-driven examples, and the Bluesky adapter), install everything:

   ```bash
   pip install -e ".[maps,example,bluesky,test]"
   ```

The optional extras map to specific features:

| Extra       | Pulls in         | Enables                                                        |
| ----------- | ---------------- | ------------------------------------------------------------- |
| `maps`      | `folium`         | The interactive `MapVisualizer` HTML map output               |
| `bluesky`   | `atproto`        | `read_bluesky` and `BlueskyFetcher` (Bluesky / AT Protocol)   |
| `example`   | `python-dotenv`  | Loading API credentials from a `.env` file in the examples    |
| `test`      | `coverage`       | Coverage measurement for the test suite                       |

The core readers, analysis, extraction, and GeoJSON export layers depend only on the Python standard library, so most contributions need nothing beyond the standard install plus `test`.

Note: the base install currently pulls in `tweepy`, which backs the X (Twitter) API v2 fetcher. The pure standard-library readers (`read_csv`, `read_geojson`, `read_records`, `load_sample`) never touch it.

## Running the checks

Before opening a pull request, run the same checks that CI runs. If they all pass locally, the PR will pass CI.

### Tests

The suite is plain `unittest` and is fully network-free (the provider clients for X and Bluesky are mocked), so it runs offline and deterministically:

```bash
python -m unittest discover -s tests -v
```

### Coverage

CI enforces a coverage gate of at least 90 percent, scoped to the `geosocialx` package. Reproduce it locally:

```bash
coverage run -m unittest discover -s tests
coverage report --fail-under=90
```

If you add code, add tests that cover it so the gate stays green. New tests live in `tests/` and follow the existing files: `test_sources.py`, `test_geospatial.py`, `test_data_fetcher.py`, and `test_bluesky.py`. Keep tests offline: mock any network client rather than calling a real API.

### Lint and formatting

Formatting and linting use [ruff](https://docs.astral.sh/ruff/) (configured in `pyproject.toml`, line length 88):

```bash
ruff format .        # apply formatting
ruff check .         # lint (import order and common errors)
```

CI runs `ruff format --check .` and `ruff check .`, so make sure both are clean.

### Type checking

The package ships type hints and is marked `py.typed` (PEP 561). Type-check with mypy:

```bash
mypy geosocialx
```

The mypy configuration lives in `pyproject.toml` and already ignores missing stubs for the optional third-party clients (`tweepy`, `folium`, `dotenv`, `atproto`).

## Design principles

A few conventions keep the package small and predictable. Please keep them in mind when proposing changes:

1. **The core stays standard-library only.** The extraction, source readers, analysis, and GeoJSON export layers must not import third-party packages. If a feature genuinely needs a heavy dependency, put it behind a new optional extra (as `maps`, `bluesky`, and `example` already are) and import it lazily inside the function that uses it, so the core import path stays dependency-free.
2. **Everything normalises to `GeoRecord`.** New data sources should return `GeoRecord` objects (or lists of them) so that the analysis and visualization layers work unchanged, regardless of where the data came from.
3. **Be honest about geography.** Coverage statistics distinguish exact coordinates from place-level and no-geo records. Preserve that honesty: skip malformed or out-of-range coordinates rather than silently coercing them, and do not overstate precision.
4. **Respect service Terms of Service.** The X and Bluesky fetchers must stay within the terms of the APIs they call. Do not add functionality that scrapes or circumvents rate limits or authentication.

## Pull request workflow

1. Create a feature branch off `main`:

   ```bash
   git checkout -b my-feature
   ```

2. Make your change, and add or update tests for it.
3. Run the full local check set (tests, coverage gate, `ruff format`, `ruff check`, `mypy`). All should pass.
4. Update `CHANGELOG.md` under an `Unreleased` heading, following the existing [Keep a Changelog](https://keepachangelog.com/) style, if your change is user-visible.
5. Update the README or docstrings if you changed public behavior or added a public function.
6. Commit with a clear message, push to your fork, and open a pull request against `JayeshSuryavanshi/GeoSocialX:main`. Describe what the change does and link any related issue.

Keep pull requests focused: one logical change per PR is much easier to review than a large mixed one. Draft PRs are welcome if you want early feedback.

## Coding conventions

- Target Python 3.10 and above. Use modern typing syntax (`str | None`, `list[GeoRecord]`).
- Add type hints to every public function and method signature.
- Write a docstring for every public function, class, and method. Match the existing style: a one-line summary, then a short prose description of the parameters and behavior, using double-backtick markup for names and types (see `geosocialx/sources.py` for examples). This keeps the API documentation coherent since the docstrings are the API reference.
- Follow the formatting ruff applies; do not hand-format around it.
- Prefer clear, small functions over comments. Add a comment only where the logic is genuinely non-obvious.

## Documentation

GeoSocialX does not host a separate documentation site yet. Its documentation lives in three places, and all three count:

- The **README**, which covers the overview, install, quickstart, and a per-module API tour.
- **Docstrings** on every public function and class (the API reference).
- The **`examples/`** directory: `quickstart.ipynb` and `coverage_worked_example.py` are runnable, worked tutorials.

When you change public behavior, update whichever of these are affected. If you add a public function, give it a docstring with at least one usage example, and consider adding a short snippet to the README's API section.

## Reporting a security issue

Please do not open a public issue for security problems (for example, credential handling in the fetchers, or anything that could expose a user's API tokens).

Instead, report it privately through GitHub's private vulnerability reporting: go to the repository's **Security** tab and choose **Report a vulnerability**, which opens a private advisory visible only to the maintainer. If that is unavailable to you, email the maintainer at the address listed in `CITATION.cff` / `pyproject.toml` and include "GeoSocialX security" in the subject. You will get an acknowledgement, and a fix and disclosure timeline will be coordinated with you before any public discussion.

## Releases

Releases are automated. Pushing a version tag of the form `vX.Y.Z` that matches the `version` in `pyproject.toml` triggers the release workflow, which builds the package and publishes it to PyPI using Trusted Publishing (OIDC, no stored API token). Contributors do not need to publish anything; maintainers cut releases from `main`. The `CHANGELOG.md` is the record of what went into each version.

## Recognition and licensing

By contributing, you agree that your contributions are licensed under the project's [MIT License](LICENSE), the same terms as the rest of GeoSocialX.

If you use GeoSocialX in academic work, please cite it: see `CITATION.cff` and the Zenodo DOI [10.5281/zenodo.21726579](https://doi.org/10.5281/zenodo.21726579). Contributors who make a substantial addition are welcome to add themselves to the citation metadata as part of their pull request.

Thank you for helping make GeoSocialX better.
