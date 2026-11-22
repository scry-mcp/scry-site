# scry-site

This repository builds the SCRY site from the SCRY repositories' own documents. The site has a
home, a page per tool of each server, a page per demo with its clip moving, a page on the
knowledge base, and every other public document. Every word about a server is read from its repository at build time.

The site's own words are in its templates (`scry_site/templates/`) and in the modules that
build each kind of page: `home.py`, `demos.py`, `reference.py` and `build.py` in `scry_site/`.

## Build it

You need git, [uv](https://docs.astral.sh/uv/), and one directory holding checkouts of
[scry-core](https://github.com/scry-mcp/scry-core),
[scry-mame](https://github.com/scry-mcp/scry-mame) and
[scry-dosbox-x](https://github.com/scry-mcp/scry-dosbox-x) under those names. With this
repository cloned beside them:

```sh
uv run scry-site ../ --out _site
python3 -m http.server --directory _site 8000
```

The first line prints one line of JSON: the pages written, the files copied, and the links
inside the site it followed. The second serves the site at `http://localhost:8000`.

## What a build refuses

A build renders into a directory beside `--out` and puts it in place only once every check
passes. Otherwise it leaves `--out` as it was, prints `INVALID:` with the reason, and exits 3.

It stops at the first source that is not in the shape the site reads. In a server's `README.md`:

- no `<h1>`, or no bold opening sentence;
- an `## Install` that does not open with a sentence and a `sh` block;
- no install block (`<!-- scry-install:begin -->`), a client in it without its sentence and
  one fenced block, or two READMEs listing different clients;
- a `### Your first question` without exactly one quoted prompt;
- a `## What you can ask` item that is not a bold question, its tools and a sentence, or that
  names a tool with no entry in the reference;
- a `## See it run` that does not list each demo;
- in scry-dosbox-x's, no `demo-lead` block with its picture and the rows "You ask", "Your
  client calls" and "SCRY answers".

In the reference:

- `REFERENCE.md` without its generated index, an index entry naming a page that is not tracked
  or is named `index`, or a page in `docs/reference/` the index does not list;
- a tool's entry that does not open with its name, one sentence and its signature;
- an entry whose sections are not, in order, Try it, modes (optional), Arguments, What comes
  back, What it refuses, Why it works this way and Related tools;
- one tool with two entries.

In a demo's `README.md`:

- no motion block, or one whose moments disagree with their times or with the frames of
  `loop.webp`;
- a `loop.webp` that is not an animated WebP, or a `loop.webp` or `screen.png` not tracked;
- no single transcript block of numbered steps;
- a demo folder named outside lowercase letters, digits, `_` and `-`.

In a server's knowledge base, which the build asks by running that checkout's own loader
(`scry_site/knowledge.py` names where each server keeps it):

- a base that does not load, one that serves no entry, or one that reports faults, each named
  by its repository;
- a `knowledge_find` example whose whole reply is not one named entry, which is what the home
  and the knowledge base page show it by.

An example is on a tool's page or a demo's. It must be the request, its quote, one or two calls
each with its reply, a sentence reading the reply, and the whole reply folded.

A build also stops on a page without a title, and on scry-core's `## Credits` not being the one
credits line. The READMEs link the author's LinkedIn there; the site links their GitHub instead,
and a build refuses any other link to LinkedIn in a source. It refuses an `--out` that names a file, the checkouts' directory or a place in
one, or a directory holding files no build made.

It lists every one of these:

- a link in any source to a path its repository does not track, named by file and link;
- a link inside the built site to a page it does not hold, or to a heading that page does not
  carry, named by the built page.

## What the pages are made of

- `scry_site/sources.py` reads the sources and each part of a README the home takes.
- `scry_site/reference.py` cuts each family's page into one page per tool and the family's own
  page. A link to a tool's heading goes to that tool's page.
- `scry_site/example.py` draws every example in one shape and every code block in a framed box.
- `scry_site/motion.py` reads a demo's `loop.webp`: its size, which sets the screen frame it
  plays in, and its frame times, which light each moment while it plays.
- `scry_site/home.py` and `scry_site/demos.py` fill the home and each demo's page.
- `scry_site/knowledge.py` asks each checkout's base what it serves, and draws
  the home's knowledge base section, the page of its own and the reference index's sentence.
  The counts are never typed. The loader runs in a process of its own with the checkouts'
  `src` folders alone on its path, so the base must need only the standard library.
- `scry_site/render.py` renders markdown with GitHub's heading anchors, and points each
  relative link at its page here, at a copy of the file, or at the file on GitHub.
- `scry_site/check.py` follows every link inside the built site.
- `scry_site/seo.py` writes what search engines and AI crawlers read: each page's canonical
  address and social tags, the home's structured data, `robots.txt` (which names the AI
  crawlers it welcomes) and `sitemap.xml`. It also holds the IndexNow key, a public value the
  build serves as `<key>.txt`; the publish workflow sends the sitemap's addresses to
  IndexNow after each publish, and a failure there does not fail the run.
- `scry_site/analytics.py` and `scry_site/static/consent.js` ask the visitor before measuring
  with Google Analytics, and write the privacy and cookies pages. A build with no
  `SCRY_GA4_ID` in its environment has no banner, no tag and no measurement; the id is the
  property's `G-` value, public by nature since it travels in the page.
- `scry_site/build.py` puts it together. It also writes a markdown copy of every page made from
  a whole document, `llms.txt`, which lists those copies and the knowledge base page, and `404.html`, the page served for
  any address that holds none.
- `scry_site/templates/` and `scry_site/static/` are the layout and the look. The fonts are
  served with the site under the SIL Open Font License (`scry_site/static/fonts/`).

## Checks

```sh
uv run ruff check .
uv run mypy --strict .
uv run pytest -q
```

Most tests build sites from small git repositories they create. `tests/test_real.py` builds
the site from the real checkouts and checks it against the design rules:

- every text's contrast, computed from `site.css`;
- the number of words on the home above its install block;
- in a headless Chrome, at 390 and 1440 px: no page scrolls sideways, no code block is wider
  than its box, and no text is under 13 px;
- at the end of a command page, the tool list in reach: on a wide screen the open command, the
  section being read and the next command show in it; on a phone the corner link shows, takes
  the reader to the list opened, and hides no focused control;
- at the end of a command or family page, the list's way up to the server's reference shows
  without scrolling the page back, and its last group holds every family of the server;
- at the end of a family or document page in a short window, the wide side list sits between
  the bar and the foot;
- on a phone, every link of a page's crumbs is 44 px high;
- on a phone, the side list opened ends above the text;
- a focused link in the wide tool list, and its way up, shows its whole focus ring.

It finds the checkouts in `SCRY_SITE_CHECKOUTS`, else in `repos/`, else in the directory this
repository sits in. It finds Chrome in `SCRY_SITE_CHROME`, else on the `PATH`, else where macOS
installs it. Without either, it fails.

## Publishing

The site is served at [scryai.net](https://scryai.net/), and nothing goes there by itself:
someone starts the "Deploy site" workflow by hand, on `main`, from the Actions tab or with:

```sh
gh workflow run deploy-site.yml --ref main
```

Run it whenever a server's documents change; this repository needs no new commit. The run
repeats the checks, builds from the three repositories' `main`, serves the result and clears
the cache.

Each run that builds keeps what it built as a new release, which is never written again. A release is named
by when it was built, in UTC, and this repository's commit: `20261118-153012-f10abef`. It
records the commits of this repository and of the three it was built from.

The list of releases is the run history of "Deploy site": each run's summary names its release
and those four commits. To list the runs:

```sh
gh run list --workflow deploy-site.yml
```

To go back, run it again with an earlier release's name. Nothing is rebuilt, and the site is
exactly what that release holds:

```sh
gh workflow run deploy-site.yml --ref main -f release=20261118-153012-f10abef
```

A run refuses a name it does not know, and a release whose upload never finished. Releases from
before this naming, named by a commit alone, stay stored but cannot be served again.

The property's id comes from the repository variable `SCRY_GA4_ID`; without it the published
site measures nothing. After each publish the workflow also tells IndexNow, the protocol Bing
and other engines read, which pages are served; the key it uses is public and is served at the
site's root.

A pull request and every push to `main` run the checks and the build in `ci.yml`. Both
workflows clone the three repositories without a token, so they must stay public.

## Licence

MIT. See `LICENSE`. The fonts keep their own licence, beside them.

## Credits

Developed by Optimiza ([Marcos Hernández](https://www.linkedin.com/in/optimiza/)), in collaboration with [MS-DOS Club](https://msdos.club) and its [podcast](https://www.ivoox.com/podcast-ms-dos-club_sq_f11160693_1.html).
