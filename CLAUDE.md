# scry-site

Context for a coding assistant working on this repository. The public documentation starts at
`README.md`; this file says what the repository is, how to check a change, and where its rules
live.

## What this repository is

The static site of SCRY. A build reads the three SCRY repositories (scry-core and the two
servers) and renders their documents into pages: the home, one page per tool, the demos and the
reference indexes. Every word the site shows about a server comes from that server's
repository; only the home's own words, the headings and the navigation are written here.
`README.md` says how to build it and what a build refuses.

## What a later session must keep true

- A family's name and its place in the navigation are read from each server's `REFERENCE.md`
  index. Never write a family name in this repository: a rename in a server reaches the site by
  itself, and a name typed here would survive it.
- A knowledge reply is shown whole. The visible pane is an excerpt within the site's line limit,
  and the whole reply sits in a closed `<details>` with nothing cut; the fields that count what
  the base holds (`served`, `held_back`) and the reading sentence that only counts them are the
  one thing left out (`scry_site/knowledge.py`).
- An example is copied from a server's `docs/reference/examples.json`, never typed.
- The reasons are in `docs/decisions.md`, one section per decision, with the date.

## Checking a change

```sh
uv run ruff check .
uv run mypy --strict .
uv run pytest -q
```

The site is published from `main` by a workflow started by hand (`README.md`, *Publishing*).

## How work is done here

- English everywhere: code, comments, documents, commit messages.
- Conventional Commits; the body says why.
- A new test is seen failing first, by breaking the line it covers.
- No new check, hook or CI step is added without the maintainers asking for it.

## Rules

Path-scoped rules live in `.claude/rules/` and load when a file they govern is opened.
