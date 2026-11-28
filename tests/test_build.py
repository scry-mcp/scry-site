from __future__ import annotations

import html
import json
import os
import re
import struct
import subprocess
from pathlib import Path

import pytest
from fixtures import (
    CREDITS,
    FOUND,
    base_files,
    core_files,
    demo_readme,
    entry,
    family,
    git_repo,
    make,
    server,
    track,
    webp,
)

from scry_site import build, example, motion, render, seo, sources
from scry_site.check import check
from scry_site.sources import Invalid


@pytest.fixture()
def repos(tmp_path: Path) -> Path:
    return make(tmp_path / "repos")


def side_of(page: str) -> str:
    """The desktop half of a page's side list."""
    start = page.index('<div class="side-d">')
    return page[start:page.index("</nav>", start)]


def built(repos: Path, tmp_path: Path, page: str) -> str:
    build.build(repos, tmp_path / "site")
    return (tmp_path / "site" / page).read_text()


def replace(f: Path, old: str, new: str) -> None:
    text = f.read_text()
    assert text.count(old) >= 1, old
    f.write_text(text.replace(old, new, 1))


def test_builds_every_page_and_lands_every_link(repos: Path, tmp_path: Path) -> None:
    report = build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    assert report["pages"] == 32
    assert report["links"] > 0
    for page in ("index.html", "404.html", "reference/index.html", "mame/index.html",
                 "mame/reference/index.html", "mame/reference/breakpoints/index.html",
                 "mame/reference/breakpoints/watch_add.html", "mame/reference/session/start.html",
                 "mame/demos/gridlee/index.html", "mame/contributing.html", "core/index.html",
                 "core/docs/file-names.html"):
        assert (site / page).is_file(), page
    assert (site / "dosbox-x/demos/monkey/loop.webp").read_bytes()[:4] == b"RIFF"
    assert (site / "fonts/fraunces-latin.woff2").is_file()
    assert (site / ".nojekyll").is_file()
    (site / "stale.html").write_text("old")
    assert build.build(repos, site) == report
    assert not (site / "stale.html").exists()


def test_main_reports_and_exits(repos: Path, tmp_path: Path,
                                capsys: pytest.CaptureFixture[str]) -> None:
    assert build.main([str(repos), "--out", str(tmp_path / "site")]) == 0
    assert json.loads(capsys.readouterr().out)["pages"] == 32
    assert build.main([str(tmp_path / "none"), "--out", str(tmp_path / "x")]) == 3
    assert capsys.readouterr().err.startswith("INVALID: no scry-mame checkout")


# ---- the credits line ------------------------------------------------------------------------

REAL_CREDITS = (
    "Developed by Optimiza ([Marcos Hernández](https://www.linkedin.com/in/optimiza/)), in "
    "collaboration with [MS-DOS Club](https://msdos.club) and its "
    "[podcast](https://www.ivoox.com/podcast-ms-dos-club_sq_f11160693_1.html).")


def with_real_credits(repos: Path) -> None:
    for name in ("scry-mame", "scry-dosbox-x", "scry-core"):
        replace(repos / name / "README.md", CREDITS, REAL_CREDITS)


def test_the_site_links_the_authors_github_wherever_a_readme_links_linkedin(
        repos: Path, tmp_path: Path) -> None:
    with_real_credits(repos)
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    for page in ("index.html", "mame/index.html", "dosbox-x/index.html", "core/index.html",
                 "core/docs/file-names.html", "mame/index.md", "core/index.md", "llms.txt"):
        text = (site / page).read_text()
        assert "linkedin" not in text.lower(), page
    for page in ("index.html", "mame/index.html", "core/index.html", "mame/index.md"):
        assert "https://github.com/Optimiza" in (site / page).read_text(), page
    # the sources keep their own line
    assert "https://www.linkedin.com/in/optimiza/" in (repos / "scry-core/README.md").read_text()


@pytest.mark.parametrize("source", [
    "scry-mame/README.md", "scry-mame/CONTRIBUTING.md", "scry-mame/demos/gridlee/README.md",
    "scry-mame/docs/reference/session.md", "scry-core/docs/file-names.md"])
@pytest.mark.parametrize("link", [
    "[x](https://www.linkedin.com/in/someone-else/)",
    "[x](https://www.linkedin&#46;com/in/someone-else/)",
    "[me](https://www.linkedin.com/in/optimiza/)"])
def test_a_linkedin_link_outside_the_credits_line_is_invalid(
        repos: Path, tmp_path: Path, source: str, link: str) -> None:
    with_real_credits(repos)
    f = repos / source
    f.write_text(f.read_text() + f"\n{link}\n")
    with pytest.raises(Invalid, match="a mention of LinkedIn"):
        build.build(repos, tmp_path / "site")


# ---- the home ------------------------------------------------------------------------------


def test_the_home_reads_every_word_about_a_server_from_its_readme(repos: Path,
                                                                 tmp_path: Path) -> None:
    home = built(repos, tmp_path, "index.html")
    assert "You need git, <a href=\"https://docs.astral.sh/uv/\">uv</a> and a MAME with its " \
           "debugger." in home
    assert '<span class="p">$ </span>git clone https://github.com/scry-mcp/scry-dosbox-x' in home
    assert "Ask your client what a DOSBox-X program is doing." in home
    # the prompt of the first question is the README's, its two lines joined
    assert "<p>Start <code>gridlee</code> and show me the screen.</p>" in home
    assert '<a href="mame/reference/breakpoints/watch_add.html">watch_add</a>' in home


def test_the_install_shows_each_client_block_the_readme_carries(repos: Path,
                                                               tmp_path: Path) -> None:
    home = built(repos, tmp_path, "index.html")
    assert home.count('name="cli"') == 2
    assert 'id="cli-claude-code" checked>Claude Code' in home and 'id="cli-cursor">Cursor' in home
    assert 'claude mcp add <span class="nb">--scope</span> user mame' in home
    assert '<span class="k">&quot;mcpServers&quot;</span>' in home
    assert '.install:has(#cli-cursor:checked) .panel[data-cli="cursor"]' in home
    assert ".install:has(#srv-mame:checked) .for-dosbox-x" in home


def test_two_readmes_listing_different_clients_are_invalid(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/README.md", "<summary>Cursor</summary>", "<summary>Zed</summary>")
    with pytest.raises(Invalid, match="different clients"):
        build.build(repos, tmp_path / "site")


def test_the_hero_is_the_dosbox_x_lead_with_its_moments_lit(repos: Path, tmp_path: Path) -> None:
    home = built(repos, tmp_path, "index.html")
    assert '<figure class="shot timed" style="max-width:640px">' in home
    assert 'srcset="dosbox-x/demos/monkey/screen.png"' in home
    assert '<img src="dosbox-x/demos/monkey/loop.webp" width="640" height="400" ' \
           'alt="The monkey demo moving">' in home
    assert "<b>You</b><span class=said>Write the line.</span>" in home
    assert "<b>SCRY</b><span><code>{&quot;verified&quot;: true}</code></span>" in home \
        or '<b>SCRY</b><span><code>{"verified": true}</code></span>' in home
    # the second moment starts a quarter in: 1000 of 4000 ms
    assert "@keyframes take-2{0%{color:var(--muted)}25.00%{color:var(--fg)}100%" in home
    assert "MONKEY 0:04" in home


def test_a_hero_whose_picture_has_another_count_of_moments_is_invalid(repos: Path,
                                                                     tmp_path: Path) -> None:
    f = repos / "scry-dosbox-x/demos/monkey/README.md"
    replace(f, "2. `state_write` loads the\n   saved state.\n", "")
    replace(f, "<!-- moments-ms: 1000,3000 -->", "<!-- moments-ms: 4000 -->")
    with pytest.raises(Invalid, match="the hero names 2 moments"):
        build.build(repos, tmp_path / "site")


def test_a_demo_both_servers_run_is_one_card_that_names_both(repos: Path, tmp_path: Path) -> None:
    for name in ("scry-mame", "scry-dosbox-x"):
        repo = repos / name
        track(repo, "demos/lineup/README.md", demo_readme("lineup"))
        track(repo, "demos/lineup/screen.png", b"\x89PNG")
        track(repo, "demos/lineup/loop.webp", webp(640, 400, (4000,)))
        replace(repo / "README.md", "## Platforms",
                "- [`demos/lineup/`](demos/lineup/): lineup, played.\n\n## Platforms")
    home = built(repos, tmp_path, "index.html")
    assert home.count("<b>Lineup</b>") == 1
    assert '<small class="on">MAME · DOSBox-X</small>' in home
    monkey = (tmp_path / "site/dosbox-x/demos/monkey/index.html").read_text()
    assert 'href="../lineup/index.html"' in monkey


def test_a_demo_the_readme_does_not_list_is_invalid(repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-mame", "demos/extra/README.md", demo_readme("extra"))
    track(repos / "scry-mame", "demos/extra/screen.png", b"\x89PNG")
    track(repos / "scry-mame", "demos/extra/loop.webp", webp(640, 400, (4000,)))
    with pytest.raises(Invalid, match="'See it run' does not list demos/extra/"):
        build.build(repos, tmp_path / "site")


def test_an_ask_naming_a_tool_with_no_entry_is_invalid(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/README.md", "`scan`, `watch_add`.", "`gone`.")
    with pytest.raises(Invalid, match="names `gone`"):
        build.build(repos, tmp_path / "site")


def test_an_ask_the_home_does_not_show_is_held_to_the_reference_too(repos: Path,
                                                                   tmp_path: Path) -> None:
    more = "".join(f'- **"Question {i}?"** `scan`. It answers.\n' for i in range(3))
    replace(repos / "scry-mame/README.md", "\n## See it run",
            more + '- **"And this?"** `gone`. It answers.\n\n## See it run')
    with pytest.raises(Invalid, match="names `gone`"):
        build.build(repos, tmp_path / "site")


def test_words_after_the_last_question_are_invalid(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/README.md", "A scan narrows it.\n",
            "A scan narrows it.\n\nClosing words.\n")
    with pytest.raises(Invalid, match="not a list of"):
        build.build(repos, tmp_path / "site")


def test_a_client_with_two_code_blocks_is_invalid(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/README.md", "</details>",
            "\n\nOr this.\n\n```json\n{}\n```\n\n</details>")
    with pytest.raises(Invalid, match="read as a name, a sentence and a fenced block"):
        build.build(repos, tmp_path / "site")


def test_a_lead_naming_a_demo_the_server_does_not_have_is_invalid(repos: Path,
                                                                 tmp_path: Path) -> None:
    f = repos / "scry-dosbox-x/README.md"
    f.write_text(f.read_text().replace("demo-lead:begin monkey", "demo-lead:begin nosuch")
                 .replace("demo-lead:end monkey", "demo-lead:end nosuch")
                 .replace("demos/monkey/loop.webp", "demos/nosuch/loop.webp"))
    with pytest.raises(Invalid, match="its lead shows demos/nosuch/, which has no page"):
        build.build(repos, tmp_path / "site")


@pytest.mark.parametrize(("path", "old", "new", "message"), [
    ("scry-mame/README.md", "## Install", "## Setup", "no section '## Install'"),
    ("scry-mame/README.md", "```sh\ngit clone", "```bash\ngit clone",
     "does not open with a sentence and a ```sh block"),
    ("scry-mame/README.md", "<!-- scry-install:begin -->", "",
     "no '<!-- scry-install:begin -->'"),
    ("scry-mame/README.md", "### Your first question", "### First",
     "no section '### Your first question'"),
    ("scry-mame/README.md", "> Start", "Start", "holds 0 quoted prompts"),
    ("scry-mame/README.md", '- **"Who writes this byte?"**', "- Who", "not a list of"),
    ("scry-mame/README.md", "- [`demos/gridlee/`]", "- [gridlee]", "lists no"),
    ("scry-mame/README.md", "<p align=\"center\"><b>", "<p><b>", "no bold opening sentence"),
    ("scry-mame/README.md", "<h1 align=\"center\">", "<div>", "no level-one heading"),
    ("scry-dosbox-x/README.md", "demo-lead:begin monkey", "lead monkey",
     "no '<!-- demo-lead:begin <demo> -->'"),
    ("scry-dosbox-x/README.md", "Your client calls", "It calls", "the rows You ask"),
    ("scry-mame/README.md", "</details>\n<!-- scry-install:end", "\n<!-- scry-install:end",
     "holds 2 clients and 1 read"),
    ("scry-mame/REFERENCE.md", "scry-reference:begin index", "index",
     "no '<!-- scry-reference:begin index -->'"),
    ("scry-mame/CONTRIBUTING.md", "# Contributing", "Contributing", "no level-one heading"),
    ("scry-core/README.md", "## Credits", "## Thanks", "no section '## Credits'"),
    ("scry-core/README.md", "Developed by", "Made by", "must hold one line"),
    ("scry-mame/demos/gridlee/README.md", "<!-- moments-ms: 1000,3000 -->",
     "<!-- moments-ms: 1000,2000 -->", "the moments last 3000 ms and the picture 4000 ms"),
    ("scry-mame/demos/gridlee/README.md", "<!-- moments-ms: 1000,3000 -->",
     "<!-- moments-ms: 4000 -->", "names 2 moments and times 1"),
    ("scry-mame/demos/gridlee/README.md", "<!-- demo-motion:begin -->", "",
     "no '<!-- demo-motion:begin -->'"),
    ("scry-mame/demos/gridlee/README.md", "### 1. Find the credits", "### Find the credits",
     "not a list of '### N. Title' steps"),
    ("scry-mame/demos/gridlee/README.md", "Ask:\n\n> Find", "Ask:\n\nFind", "the example is not"),
    ("scry-mame/demos/gridlee/README.md", "Reply, 1 of 4 fields:", "Answer:", "the example is not"),
    ("scry-mame/demos/gridlee/README.md", "```text\nscan(", "```json\nscan(",
     "a ```text block was expected"),
    ("scry-mame/demos/gridlee/README.md", "<details><summary>The whole reply", "<div><summary>",
     "the example is not"),
    ("scry-mame/demos/gridlee/README.md", '<img src="loop.webp"', '<img src="other.webp"',
     "the motion block has no"),
    ("scry-mame/demos/gridlee/README.md", "<!-- demo-transcript:end -->",
     "<!-- demo-transcript:end -->\n<!-- demo-transcript:end -->", "no single"),
    ("scry-mame/docs/reference/session.md", "### Try it", "Words.\n\n### Try it",
     "holds text before its first '### '"),
    ("scry-mame/docs/reference/session.md", "### What it refuses",
     "#### A note\n\n### What it refuses", "holds headings other than"),
    ("scry-mame/docs/reference/session.md", "- [`start`](session.md#start)",
     "- [`start`](/session.md#start)", "(outside the repository)"),
    ("scry-mame/README.md", "cd scry-mame\n```", "cd scry-mame\n``` trailing",
     "a fenced block was expected"),
])
def test_a_source_the_site_reads_from_is_required(repos: Path, tmp_path: Path, path: str,
                                                  old: str, new: str, message: str) -> None:
    replace(repos / path, old, new)
    with pytest.raises(Invalid, match=re.escape(message)):
        build.build(repos, tmp_path / "site")


def test_a_missing_checkout_is_invalid(repos: Path, tmp_path: Path) -> None:
    (repos / "scry-core/README.md").unlink()
    with pytest.raises(Invalid, match="no scry-core checkout"):
        build.build(repos, tmp_path / "site")


# ---- a tool's page -------------------------------------------------------------------------


def test_a_tool_has_its_own_page_with_the_example_first(repos: Path, tmp_path: Path) -> None:
    page = built(repos, tmp_path, "dosbox-x/reference/breakpoints/watch_add.html")
    assert '<span class="tag dos">DOSBox-X</span><span class="tag">Breakpoints</span>' in page
    assert '<h1 class="cmd-name">watch_add</h1>' in page
    assert '<p class="sig">watch_add(ref, mode=&quot;show&quot;)</p>' in page
    order = [page.index(f'<h2 id="{i}">') for i in (
        "try-it", "the-two-modes", "arguments", "what-comes-back", "what-it-refuses",
        "why-it-works-this-way", "related-tools")]
    assert order == sorted(order)
    assert '<figcaption>On the demo, stopped.</figcaption>' in page
    assert '<span class="tag">Ask</span><p>Use watch_add on the score.</p>' in page
    assert '<div class="pane-h">Reply <small>2 of 5 fields</small></div>' in page
    assert '<pre><code><span class="c">watch_add</span>(ref=&quot;score&quot;)' in page \
        or '<pre><code><span class="c">watch_add</span>(ref="score")' in page
    assert '<p class="then">Then let it run:</p>' in page
    assert '<dt>ref <small>string, <span class="req">required</span></small></dt>' in page
    assert '<ul class="related">' in page


def test_the_side_list_nests_the_open_tools_sections_under_it(repos: Path,
                                                             tmp_path: Path) -> None:
    page = built(repos, tmp_path, "mame/reference/breakpoints/scan.html")
    side = side_of(page)
    current = side[side.index("aria-current=page"):]
    assert current.index(">scan</a>") < current.index('<ul class=sub><li><a href="#try-it">')
    assert side.index(">watch_add</a>") < side.index(">scan</a>")
    assert "Breakpoints and watches." in side
    assert '<summary>Breakpoints: 2 tools</summary>' in page
    assert 'class="toc"' not in page


def test_a_command_page_links_back_to_its_side_list_and_a_family_page_does_not(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    tool = (tmp_path / "site/mame/reference/breakpoints/scan.html").read_text()
    assert '<nav class="side tools" id="side-list" aria-label="Breakpoints">' in tool
    main = tool[tool.index('<main id="content"'):tool.index("</main>")]
    assert main.endswith('<a class="tolist" href="#side-list">'
                         '<span aria-hidden="true">&#9650;</span> Tools</a>')
    family = (tmp_path / "site/mame/reference/breakpoints/index.html").read_text()
    assert 'id="side-list"' in family and 'class="tolist"' not in family


def test_a_tool_side_list_opens_on_the_servers_reference_and_ends_on_every_family(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    up = '<a class="up" href="../index.html"><span aria-hidden="true">&#9664;</span> ' \
         'MAME reference</a>'
    fams = ('<p class="grp">Families</p><ul><li><a href="../session/index.html">Session</a></li>'
            '<li><a aria-current=true href="index.html">Breakpoints</a></li>'
            '<li><a href="../names/index.html">Names</a></li></ul>')
    for page in ("scan.html", "index.html"):
        text = (site / "mame/reference/breakpoints" / page).read_text()
        # on a phone, first inside the folded list; on a desktop, above the list's own scroll
        assert '<summary>Breakpoints: 2 tools</summary><a class="up"' in text
        assert f'<div class="side-top">{up}</div><div class="side-d"><p>Breakpoints</p>' in text
        assert text.count(up) == 2
        assert side_of(text).endswith(f"{fams}</div>")
    docs = (site / "mame/contributing.html").read_text()
    assert 'class="up"' not in docs and "side-top" not in docs


def test_the_families_are_named_and_ordered_by_the_servers_own_index(
        repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/REFERENCE.md"
    replace(f, "- [Names](docs/reference/names.md): Names and what they mean.",
            "- [Knowledge](docs/reference/names.md): Names and what they mean.")
    page = built(repos, tmp_path, "mame/reference/session/index.html")
    assert side_of(page).split('<p class="grp">Families</p>')[1].startswith(
        '<ul><li><a aria-current=true href="index.html">Session</a></li>'
        '<li><a href="../breakpoints/index.html">Breakpoints</a></li>'
        '<li><a href="../names/index.html">Knowledge</a></li></ul>')


def test_a_tool_and_a_family_link_to_their_twin_on_the_other_server(
        repos: Path, tmp_path: Path) -> None:
    mame = repos / "scry-mame"
    scan = "[`scan`](docs/reference/breakpoints.md#scan)"
    replace(mame / "REFERENCE.md", scan, f"{scan}, [`peek`](docs/reference/breakpoints.md#peek)")
    track(mame, "docs/reference/breakpoints.md", family("Breakpoints", "watch_add", "scan", "peek"))
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"

    def twin(page: str) -> str | None:
        found = re.search(r'<a class="twin" href="([^"]+)">([^<]+)</a></p>',
                          (site / page).read_text())
        return f"{found[2]} -> {found[1]}" if found else None
    assert twin("mame/reference/breakpoints/watch_add.html") \
        == "Also in DOSBox-X -> ../../../dosbox-x/reference/breakpoints/watch_add.html"
    assert twin("dosbox-x/reference/breakpoints/watch_add.html") \
        == "Also in MAME -> ../../../mame/reference/breakpoints/watch_add.html"
    assert twin("mame/reference/breakpoints/index.html") \
        == "Also in DOSBox-X -> ../../../dosbox-x/reference/breakpoints/index.html"
    assert twin("mame/reference/breakpoints/peek.html") is None
    assert twin("dosbox-x/demos/monkey/index.html") is None


def test_a_link_to_a_tools_heading_lands_on_the_tools_page(repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    scan = (site / "mame/reference/breakpoints/scan.html").read_text()
    assert 'href="watch_add.html"' in scan and 'href="../session/start.html"' in scan
    # a family heading stays on the family's page
    assert 'href="index.html#what-each-state-means"' in scan
    index = (site / "mame/reference/index.html").read_text()
    assert 'href="session/start.html"' in index and 'href="breakpoints/scan.html"' in index


def test_a_link_to_a_section_of_a_tool_lands_on_that_section(repos: Path,
                                                             tmp_path: Path) -> None:
    track(repos / "scry-mame", "docs/reference/session.md",
          (repos / "scry-mame/docs/reference/session.md").read_text()
          + "\nSee [its arguments](breakpoints.md#arguments-1).\n")
    page = built(repos, tmp_path, "mame/reference/session/index.html")
    assert 'href="../breakpoints/scan.html#arguments"' in page


def test_the_family_page_lists_its_tools_and_keeps_its_own_text(repos: Path,
                                                               tmp_path: Path) -> None:
    page = built(repos, tmp_path, "mame/reference/breakpoints/index.html")
    assert '<h2 id="what-each-state-means">' in page
    assert '<a href="watch_add.html"><code>watch_add</code></a>' in page
    assert "<span>Do what scan does, by name.</span>" in page
    assert "Try it" not in page[page.index('<main'):]


@pytest.mark.parametrize(("old", "new", "message"), [
    ("### Arguments", "### Parameters", "has the sections"),
    ("### What it refuses\n\n- A name that matches several symbols (`ambiguous_ref`).\n\n"
     "### Why it works this way", "### Why it works this way", None),
    ("- `ref` (string, required): What to use.", "- ref: what", "is not '- `name` ...'"),
    ("Do what scan does, by name.\n\n", "", "does not open with"),
])
def test_a_tool_entry_out_of_shape_is_invalid(repos: Path, tmp_path: Path, old: str, new: str,
                                             message: str | None) -> None:
    f = repos / "scry-mame/docs/reference/breakpoints.md"
    text = f.read_text()
    at = text.index("<!-- scry-reference:begin scan -->")
    f.write_text(text[:at] + text[at:].replace(old, new, 1))
    if message is None:
        build.build(repos, tmp_path / "site")
        page = (tmp_path / "site/mame/reference/breakpoints/scan.html").read_text()
        assert 'id="what-it-refuses"' not in page
        return
    with pytest.raises(Invalid, match=re.escape(message)):
        build.build(repos, tmp_path / "site")


def test_a_tool_that_takes_no_argument_says_so(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/docs/reference/session.md",
            "- `ref` (string, required): What to use.\n"
            "- `mode` (one of `\"show\"`, `\"change\"`, default `\"show\"`): How.",
            "Takes no argument.")
    page = built(repos, tmp_path, "mame/reference/session/start.html")
    assert "<p>Takes no argument.</p>" in page


def test_two_entries_of_one_tool_are_invalid(repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-mame", "docs/reference/session.md",
          (repos / "scry-mame/docs/reference/session.md").read_text() + "\n" + entry("scan"))
    with pytest.raises(Invalid, match="two entries of `scan`"):
        build.build(repos, tmp_path / "site")


# ---- a demo's page -------------------------------------------------------------------------


def test_a_demo_page_moves_with_its_moments_and_its_steps_are_examples(repos: Path,
                                                                      tmp_path: Path) -> None:
    page = built(repos, tmp_path, "mame/demos/gridlee/index.html")
    assert '<source media="(prefers-reduced-motion: reduce)" srcset="screen.png">' in page
    assert '<img src="loop.webp" width="640" height="400" alt="gridlee in play">' in page
    assert '<div class="crt tape" style="--ar:1.3333;--pad:0.00%;max-width:640px">' in page
    assert "<li><span><code>state_write</code> loads the saved state.</span></li>" in page
    assert "<b>1</b><strong>Find the credits</strong>" in page
    assert '<span class="tag">Ask</span><p>Find the credits.</p>' in page
    assert '<p class="reads">The scan holds every byte.</p>' in page
    assert 'href="../../index.html#install"' in page
    assert 'href="../../reference/breakpoints/index.html"' in page
    assert "@keyframes take-1{0%{color:var(--fg)}0.00%{color:var(--fg)}25.00%" in page
    assert "<!-- demo-transcript" not in page


def test_a_picture_that_is_not_an_animated_webp_is_invalid(repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-mame", "demos/gridlee/loop.webp", b"RIFF\0\0\0\0WEBPVP8 ")
    with pytest.raises(Invalid, match="not an animated WebP: 0 frames"):
        build.build(repos, tmp_path / "site")


def test_a_loop_that_is_not_tracked_is_invalid(repos: Path, tmp_path: Path) -> None:
    subprocess.run(["git", "-C", str(repos / "scry-mame"), "rm", "-q", "--cached",
                    "demos/gridlee/loop.webp"], check=True)
    with pytest.raises(Invalid, match=r"scry-mame: demos/gridlee/loop\.webp is not tracked"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize(("setup", "message"), [
    ("still", r"mame: demos/gridlee/screen\.png is not tracked"),
    ("unreadable", r"cannot copy mame/demos/gridlee/screen\.png"),
    ("deleted", r"cannot read scry-mame/demos/gridlee/loop\.webp"),
    ("not_webp", r"scry-mame/demos/gridlee/loop\.webp is not a WebP file"),
])
def test_a_demo_whose_files_cannot_be_shown_is_invalid(repos: Path, tmp_path: Path, setup: str,
                                                      message: str) -> None:
    gridlee = repos / "scry-mame/demos/gridlee"
    if setup == "still":
        # the README's lead links the still, so that link goes first
        f = repos / "scry-mame/README.md"
        f.write_text(f.read_text().replace(' srcset="demos/gridlee/screen.png"', ""))
        subprocess.run(["git", "-C", str(repos / "scry-mame"), "rm", "-q", "--cached",
                        "demos/gridlee/screen.png"], check=True)
    elif setup == "unreadable":
        (gridlee / "screen.png").chmod(0)
    elif setup == "deleted":
        (gridlee / "loop.webp").unlink()
    else:
        (gridlee / "loop.webp").write_bytes(b"GIF89a")
    try:
        with pytest.raises(Invalid, match=message):
            build.build(repos, tmp_path / "site")
    finally:
        (gridlee / "screen.png").chmod(0o644)


def test_a_guide_with_no_section_under_its_picture_is_invalid(repos: Path,
                                                             tmp_path: Path) -> None:
    f = repos / "scry-mame/demos/gridlee/README.md"
    f.write_text(f.read_text().replace("\n## ", "\n### "))
    with pytest.raises(Invalid, match="nothing under the motion block is a '## ' section"):
        build.build(repos, tmp_path / "site")


@pytest.mark.parametrize(("old", "new"), [
    ("<!-- demo-motion:begin -->", "Words before the picture.\n\n<!-- demo-motion:begin -->"),
    ("<!-- moments-ms:", "Words inside the motion block.\n\n<!-- moments-ms:"),
])
def test_a_guide_s_text_the_page_would_not_show_is_invalid(repos: Path, tmp_path: Path,
                                                          old: str, new: str) -> None:
    replace(repos / "scry-mame/demos/gridlee/README.md", old, new)
    with pytest.raises(Invalid, match="the page shows only"):
        build.build(repos, tmp_path / "site")


def test_a_motion_block_closing_the_file_is_read(repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/demos/gridlee/README.md"
    text = f.read_text()
    f.write_text(text[:text.index("<!-- demo-motion:end -->")] + "<!-- demo-motion:end -->")
    with pytest.raises(Invalid, match="nothing under the motion block is a '## ' section"):
        build.build(repos, tmp_path / "site")


def test_an_index_that_links_no_family_is_invalid(repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/REFERENCE.md"
    text = f.read_text()
    begin, end = "<!-- scry-reference:begin index -->", "<!-- scry-reference:end index -->"
    f.write_text(text[:text.index(begin) + len(begin)] + "\nNone yet.\n" + text[text.index(end):])
    with pytest.raises(Invalid, match="links no 'docs/reference/<family>.md'"):
        build.build(repos, tmp_path / "site")


def test_a_demo_folder_named_outside_the_site_s_names_is_invalid(repos: Path,
                                                                tmp_path: Path) -> None:
    track(repos / "scry-mame", "demos/Big Demo/README.md", demo_readme("big"))
    with pytest.raises(Invalid, match="demo directories named outside"):
        build.build(repos, tmp_path / "site")


def test_an_example_of_three_calls_is_invalid() -> None:
    pair = 'Call:\n\n```text\nresume()\n```\n\nReply:\n\n```json\n{"a": 1}\n```\n\n'
    md = (f"Ask:\n\n> Run it.\n\n{pair}Then:\n\n{pair}Then:\n\n{pair}"
          "It ran.\n\n<details><summary>All</summary>\n\nx\n\n</details>\n")
    with pytest.raises(Invalid, match="one or two 'Call:'"):
        example.parse(md, "x", located=False)
    two = md.replace(f"Then:\n\n{pair}", "", 1)
    assert len(example.parse(two, "x", located=False).calls) == 2


def test_an_example_with_nothing_in_it_is_invalid() -> None:
    with pytest.raises(Invalid, match="the example is not where, 'Ask:'"):
        example.parse("", "x", located=True)


def test_a_reply_value_and_a_line_that_is_no_call_keep_their_colours() -> None:
    assert example.json_code('{"status": "INVALID"}') == \
        '{<span class="k">&quot;status&quot;</span>: <span class="bad">&quot;INVALID&quot;</span>}'
    assert example.call_code("10 items") == "10 items"
    assert example.pane("text", "plain words") == (
        '<div class="pane"><div class="pane-h">Text</div><pre><code>plain words</code></pre>'
        "</div>")


@pytest.mark.parametrize(("width", "height", "aspect"), [
    (960, 600, 4 / 3), (512, 480, 4 / 3), (1024, 760, 4 / 3), (960, 432, 50 / 27)])
def test_a_full_screen_fills_a_4_3_tube_and_a_band_keeps_its_pixel_shape(
        width: int, height: int, aspect: float) -> None:
    assert motion.Clip(width, height, (1000,)).aspect == pytest.approx(aspect)


def test_a_clip_is_read_from_its_chunks(tmp_path: Path) -> None:
    f = tmp_path / "a.webp"
    f.write_bytes(webp(960, 432, (40, 60, 4608)))
    c = motion.clip(f, "a.webp")
    assert (c.width, c.height, c.ms, c.length()) == (960, 432, 4708, "0:05")


# ---- sources, links, twins ------------------------------------------------------------------


def test_a_chunk_of_odd_length_is_padded_to_the_next_one(tmp_path: Path) -> None:
    data = webp(320, 200, (1000, 2000))
    exif = b"EXIF" + struct.pack("<I", 3) + b"abc" + b"\0"
    body = data[12:]
    vp8x_end = 8 + 10
    odd = body[:vp8x_end] + exif + body[vp8x_end:]
    f = tmp_path / "odd.webp"
    f.write_bytes(b"RIFF" + struct.pack("<I", 4 + len(odd)) + b"WEBP" + odd)
    c = motion.clip(f, "odd.webp")
    assert (c.width, c.height, c.frames_ms) == (320, 200, (1000, 2000))


def test_an_out_that_holds_something_no_build_made_is_refused_and_kept(
        repos: Path, tmp_path: Path) -> None:
    """`--out` is replaced whole: a directory a build did not make (the site's own checkout, a
    home) would be deleted with everything in it."""
    out = tmp_path / "mine"
    out.mkdir()
    (out / "keep.txt").write_text("mine")
    with pytest.raises(Invalid, match=r"--out .*mine holds files no build made"):
        build.build(repos, out)
    assert (out / "keep.txt").read_text() == "mine"
    build.build(repos, tmp_path / "site")
    build.build(repos, tmp_path / "site")
    (tmp_path / "empty").mkdir()
    build.build(repos, tmp_path / "empty")


def test_a_tracked_symlink_is_not_followed_into_the_site(repos: Path, tmp_path: Path) -> None:
    """A tracked link is copied as the file it points at, which can be the checkout's own
    `.git/config` with the workflow's token in it."""
    mame = repos / "scry-mame"
    still = next(mame.glob("demos/*/screen.png"))
    still.unlink()
    still.symlink_to("../../.git/config")
    subprocess.run(["git", "-C", str(mame), "add", "-A"], check=True)
    with pytest.raises(Invalid, match=r"no repository tracks:\n.*gridlee/screen.png"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_a_link_to_an_untracked_path_is_invalid(repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/docs/reference/session.md"
    f.write_text(f.read_text() + "\nSee [gone](../../nowhere.md).\n")
    with pytest.raises(Invalid, match=r"scry-mame/docs/reference/session.md: \.\./\.\./nowhere.md"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_a_link_only_the_markdown_twin_resolves_is_invalid_too(repos: Path,
                                                               tmp_path: Path) -> None:
    """An unused reference definition is no link of the HTML page, but the page's markdown twin
    and `llms.txt` carry it as written."""
    f = repos / "scry-mame/docs/reference/session.md"
    f.write_text(f.read_text() + "\n[gone]: ../../nowhere.md\n")
    with pytest.raises(Invalid, match=r"scry-mame/docs/reference/session.md: \.\./\.\./nowhere.md"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_a_reference_page_the_index_misses_is_invalid_and_a_folder_under_it_is_not(
        repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-dosbox-x", "docs/reference/tour/TRANSCRIPT.md", "# The tour\n")
    build.build(repos, tmp_path / "site")
    track(repos / "scry-dosbox-x", "docs/reference/extra.md", "# Extra\n")
    with pytest.raises(Invalid, match="does not list: \\['docs/reference/extra.md'\\]"):
        build.build(repos, tmp_path / "site")


def test_an_index_naming_an_untracked_page_is_invalid(repos: Path, tmp_path: Path) -> None:
    subprocess.run(["git", "-C", str(repos / "scry-mame"), "rm", "-q", "--cached",
                    "docs/reference/session.md"], check=True)
    with pytest.raises(Invalid, match="names docs/reference/session.md, which is not tracked"):
        build.build(repos, tmp_path / "site")


def test_a_family_with_no_entry_is_invalid(repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-mame", "docs/reference/session.md", "# The Session tools\n\nNone.\n")
    with pytest.raises(Invalid, match="no '<!-- scry-reference:begin <tool> -->' entry"):
        build.build(repos, tmp_path / "site")


def test_a_family_named_index_is_invalid(repos: Path, tmp_path: Path) -> None:
    dx = repos / "scry-dosbox-x"
    replace(dx / "REFERENCE.md", "<!-- scry-reference:end index -->",
            "- [Index](docs/reference/index.md): All. [`i`](docs/reference/index.md#i)\n"
            "<!-- scry-reference:end index -->")
    track(dx, "docs/reference/index.md", "# Index\n")
    with pytest.raises(Invalid, match="'index'"):
        build.build(repos, tmp_path / "site")


@pytest.mark.parametrize("breaks", ["home", "check"])
def test_a_failed_build_leaves_the_previous_site(repos: Path, tmp_path: Path,
                                                 breaks: str) -> None:
    site = tmp_path / "site"
    build.build(repos, site)
    (site / "marker").write_text("previous")
    if breaks == "home":
        replace(repos / "scry-dosbox-x/README.md", "demo-lead:begin monkey", "x")
    else:
        f = repos / "scry-mame/docs/reference/session.md"
        f.write_text(f.read_text() + "\n[gone](breakpoints.md#nowhere)\n")
    with pytest.raises(Invalid):
        build.build(repos, site)
    assert (site / "marker").read_text() == "previous"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["repos", "site"]


@pytest.mark.parametrize("where", [".", "repos", "repos/scry-mame", "file"])
def test_out_never_replaces_the_sources_or_a_file(repos: Path, tmp_path: Path,
                                                  where: str) -> None:
    out = tmp_path / where
    if where == "file":
        out.write_text("x")
    with pytest.raises(Invalid, match="--out"):
        build.build(repos, out)
    assert (repos / "scry-mame/README.md").is_file()


@pytest.mark.parametrize(("setup", "message"), [
    ("not_git", "not a git checkout"),
    ("deleted", "cannot read scry-mame/CONTRIBUTING.md"),
    ("no_reference", "cannot read scry-mame/REFERENCE.md"),
])
def test_an_unreadable_source_is_invalid(repos: Path, tmp_path: Path, setup: str,
                                         message: str) -> None:
    mame = repos / "scry-mame"
    if setup == "not_git":
        subprocess.run(["rm", "-rf", str(mame / ".git")], check=True)
    elif setup == "deleted":
        (mame / "CONTRIBUTING.md").unlink()
    else:
        (mame / "REFERENCE.md").unlink()
    with pytest.raises(Invalid, match=message):
        build.build(repos, tmp_path / "site")


def test_names_with_digits_and_hyphens_are_pages(repos: Path, tmp_path: Path) -> None:
    dx = repos / "scry-dosbox-x"
    track(dx, "demos/speed-fight/README.md", demo_readme("speed-fight"))
    track(dx, "demos/speed-fight/screen.png", b"\x89PNG")
    track(dx, "demos/speed-fight/loop.webp", webp(640, 400, (4000,)))
    replace(dx / "README.md", "## Platforms",
            "- [`demos/speed-fight/`](demos/speed-fight/): a fight.\n\n## Platforms")
    replace(dx / "REFERENCE.md", "<!-- scry-reference:end index -->",
            "- [Gfx2](docs/reference/gfx-2.md): Pictures. [`g`](docs/reference/gfx-2.md#g)\n"
            "<!-- scry-reference:end index -->")
    track(dx, "docs/reference/gfx-2.md", family("Gfx2", "g"))
    build.build(repos, tmp_path / "site")
    assert (tmp_path / "site/dosbox-x/demos/speed-fight/index.html").is_file()
    assert (tmp_path / "site/dosbox-x/reference/gfx-2/g.html").is_file()


def test_links_land_on_the_page_the_repository_means(repos: Path, tmp_path: Path) -> None:
    mame = repos / "scry-mame"
    track(mame, "docs/diagram.svg", "<svg/>")
    f = mame / "CONTRIBUTING.md"
    f.write_text(f.read_text() + "\n[home](.) [top](./#install) [demo](demos/gridlee/) "
                 "[spaced](docs/reference/session.md#start) ![d](docs/diagram.svg) "
                 "[up](HTTPS://example.org/)\n")
    page = built(mame.parent, tmp_path, "mame/contributing.html")
    assert 'href="index.html"' in page
    assert 'href="index.html#install"' in page
    assert 'href="demos/gridlee/index.html"' in page
    assert 'href="reference/session/start.html"' in page
    assert 'src="docs/diagram.svg"' in page
    assert (tmp_path / "site/mame/docs/diagram.svg").read_text() == "<svg/>"
    assert 'href="HTTPS://example.org/"' in page


def test_a_readme_picture_and_its_still_are_copied_beside_the_page(repos: Path,
                                                                  tmp_path: Path) -> None:
    page = built(repos, tmp_path, "dosbox-x/index.html")
    assert 'srcset="demos/monkey/screen.png"' in page
    assert 'src="demos/monkey/loop.webp"' in page
    assert (tmp_path / "site/dosbox-x/demos/monkey/screen.png").is_file()


def test_a_template_key_inside_a_page_is_left_alone(repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/CONTRIBUTING.md"
    f.write_text(f.read_text() + "\nLiteral `{{credits}}` and {{body}}.\n")
    page = built(repos, tmp_path, "mame/contributing.html")
    assert "<code>{{credits}}</code> and {{body}}." in page


def test_a_wav_a_page_links_is_copied_so_the_site_plays_it(tmp_path: Path) -> None:
    base = tmp_path / "wav"
    files = server("mame", "MAME", "gridlee")
    files["demos/gridlee/README.md"] = str(files["demos/gridlee/README.md"]).replace(
        "## Run it", "Held to [music.wav](music.wav).\n\n## Run it")
    files["demos/gridlee/music.wav"] = b"RIFF"
    git_repo(base / "scry-mame", files)
    git_repo(base / "scry-dosbox-x", server("dosbox-x", "DOSBox-X", "monkey"))
    git_repo(base / "scry-core", core_files())
    build.build(base, tmp_path / "site")
    page = (tmp_path / "site/mame/demos/gridlee/index.html").read_text()
    assert 'href="music.wav"' in page
    assert (tmp_path / "site/mame/demos/gridlee/music.wav").read_bytes() == b"RIFF"


def test_every_source_page_has_a_markdown_twin_and_llms_txt_lists_them(repos: Path,
                                                                       tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    twin = (site / "mame/reference/breakpoints/index.md").read_text()
    assert twin.startswith("# The Breakpoints tools") and "(../session/index.md#start)" in twin
    readme = (site / "mame/index.md").read_text()
    assert "(demos/gridlee/index.md)" in readme
    assert "[Session](reference/index.md#the-session)" in readme
    assert not (site / "mame/reference/breakpoints/scan.md").exists()
    llms = (site / "llms.txt").read_text()
    assert llms.startswith("# SCRY\n\n> ")
    assert "- [The Breakpoints tools](mame/reference/breakpoints/index.md): " in llms
    assert "## MAME\n" in llms and "## scry-core\n" in llms


def test_the_page_doc_side_lists_the_repositorys_pages_with_the_open_ones_sections(
        repos: Path, tmp_path: Path) -> None:
    page = built(repos, tmp_path, "mame/index.html")
    side = side_of(page)
    assert '<a aria-current=page href="index.html">scry-mame</a><ul class=sub>' in side
    assert '<a href="#install">Install</a>' in side
    assert side.index(">Overview<") < side.index(">Demos<") < side.index(">Reference<")


def test_no_page_says_the_readme_as_a_link_or_an_entry(repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    for page in sorted(site.rglob("*.html")):
        assert ">The README</a>" not in page.read_text(), page
    home = (site / "index.html").read_text()
    menus = re.findall(r'<ul class="menu">(.*?)</ul>', home, re.S)
    assert len(menus) == 2
    for menu in menus:
        assert re.findall(r"<li><a [^>]*>([^<]+)</a></li>", menu) == [
            "Install", "Reference", "Demos", "GitHub"]
    core = (site / "core/docs/file-names.html").read_text()
    assert '<a href="../index.html">scry-core</a>' in side_of(core)


def test_a_page_describes_itself_by_its_first_paragraph(repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    core = (tmp_path / "site/core/index.html").read_text()
    assert '<meta name="description" content="Shared.">' in core
    tool = (tmp_path / "site/mame/reference/breakpoints/scan.html").read_text()
    assert '<meta name="description" content="Do what scan does, by name.">' in tool


def test_a_hash_line_inside_a_fence_is_no_heading_and_no_section_edge() -> None:
    md = "```sh\n# a comment, not a title\n## Not a section\n```\n\n# Real title\n\n" \
         "## Real\nbody\n```\n## inside\n```\nstill real\n\n## Next\n"
    assert sources.title_of(md, "x") == "Real title"
    assert sources.section(md, "Real", "x") == "body\n```\n## inside\n```\nstill real\n\n"
    with pytest.raises(Invalid):
        sources.section(md, "Not a section", "x")
    with pytest.raises(Invalid):
        sources.title_of("```\n# only in a fence\n```\n", "x")


def test_a_front_door_is_titled_by_the_text_of_its_h1() -> None:
    md = '<h1 align="center">\n  <img src="logo.png" alt="SCRY"><br>\n  scry-mame\n</h1>\n'
    assert sources.title_of(md, "x") == "scry-mame"


def test_a_line_break_character_that_is_not_a_newline_ends_no_line() -> None:
    md = "# T\n\nword\x0b```x\n\n## Section\nbody\n"
    assert sources.section(md, "Section", "x") == "body\n"


def test_a_fence_in_a_list_item_is_code_however_far_it_is_indented() -> None:
    md = "- item\n\n    ```\n    [home](README.md)\n    ```\n\n[home](README.md)\n"
    assert sources.masked(md).count("[home](README.md)") == 1


def _page(markdown: str) -> sources.Page:
    repo = sources.Repo("mame", "scry-mame", "MAME", Path("."))
    return sources.Page(repo, "README.md", "mame/index.html", "overview", markdown,
                        title="Title")


def test_a_bullet_list_is_no_description_and_emphasis_is() -> None:
    assert build.describe(_page("# Title\n\n* only a list\n")) == "Title"
    assert build.describe(_page("# Title\n\n*Emphasised* words\n")) == "Emphasised words"


@pytest.mark.parametrize("rule", ["***", "___"])
def test_a_thematic_break_is_no_description(rule: str) -> None:
    assert build.describe(_page(f"# Title\n\n{rule}\n\nThe real paragraph.\n")) \
        == "The real paragraph."


def test_a_long_first_paragraph_is_cut_at_a_word_and_a_page_without_one_has_its_title() -> None:
    words = " ".join(["word"] * 80)
    cut = build.describe(_page(f"# Title\n\n```\ncode\n```\n\n{words}.\n"))
    assert len(cut) <= 201 and cut.endswith("word…"), cut
    assert build.describe(_page("# Title\n\n- only a list\n")) == "Title"


def test_a_fenced_block_is_a_pane_and_a_shell_line_hangs_under_its_command() -> None:
    out = render.markdown("```sh\nclaude mcp add --scope user x\n# a note\n```\n")
    assert out.startswith('<div class="pane"><div class="pane-h">Shell</div><pre data-copy>')
    assert '<span class="l"><span class="p">$ </span>claude mcp add <span class="nb">--scope' \
           "</span> user x</span>" in out
    assert '<span class="l d"># a note</span>' in out
    reply = render.markdown('```json\n{"a": 1, "ok": "ok", "s": "x"}\n```\n')
    assert '<span class="k">&quot;a&quot;</span>: <span class="n">1</span>' in reply
    assert '<span class="ok">&quot;ok&quot;</span>' in reply and ': &quot;x&quot;}' in reply


def test_a_details_block_folds_like_every_other() -> None:
    assert '<details class="whole"><summary>' in render.markdown(
        "<details><summary>More</summary>\n\nText.\n\n</details>\n")


# ---- twins and the link check ---------------------------------------------------------------


def test_a_code_block_s_language_is_text_in_its_title() -> None:
    out = render.markdown("```<b>x\ny\n```\n")
    assert '<div class="pane-h">&lt;B&gt;X</div>' in out
    assert '<div class="pane-h">Shell</div>' in render.markdown("```sh\tlabel\ny\n```\n")


def test_html_shown_in_a_code_block_is_text_and_no_link(repos: Path, tmp_path: Path) -> None:
    replace(repos / "scry-mame/CONTRIBUTING.md", "Run the checks.",
            'Run the checks.\n\n```html\n<img src="nope.png" id="here"><a href="#top">x</a>\n```')
    build.build(repos, tmp_path / "site")
    page = (tmp_path / "site/mame/contributing.html").read_text()
    assert "&lt;img src=&quot;nope.png&quot; id=&quot;here&quot;&gt;" in page


def test_a_link_in_a_fenced_block_of_a_twin_is_code_and_stays_as_written() -> None:
    links = render.Links({("mame", "README.md"): "mame/index.html"}, {"mame": {"README.md"}})
    twin = render.twin(_page("[home](README.md)\n\n```\n[home](README.md)\n```\n"), links)
    assert twin == "[home](index.md)\n\n```\n[home](README.md)\n```\n"


def _twin(markdown: str, tracked: tuple[str, ...] = ("README.md", "REFERENCE.md",
                                                   "screen.png")) -> str:
    links = render.Links({("mame", "README.md"): "mame/index.html",
                          ("mame", "REFERENCE.md"): "mame/reference/index.html"},
                         {"mame": set(tracked)})
    out = render.twin(_page(markdown), links)
    assert links.broken == []
    return out


@pytest.mark.parametrize(("source", "want"), [
    ("[![a](screen.png)](REFERENCE.md)", "[![a](screen.png)](reference/index.md)"),
    ("[home](README.md 'the home')", "[home](index.md 'the home')"),
    ("[home](README.md (the home))", "[home](index.md (the home))"),
    ("[home](<README.md> \"t\")", "[home](<index.md> \"t\")"),
    ("[home](\n  README.md\n)", "[home](\n  index.md\n)"),
    ("`[home](README.md)` and [home](README.md)", "`[home](README.md)` and [home](index.md)"),
    ("``a ` [home](README.md) ``", "``a ` [home](README.md) ``"),
    ("[home][h]\n\n[h]: README.md\n", "[home][h]\n\n[h]: index.md\n"),
    ("[h]: <README.md> 'the home'\n\n[home][h]", "[h]: <index.md> 'the home'\n\n[home][h]"),
    ("<https://example.org/a> and [x](https://example.org/b)",
     "<https://example.org/a> and [x](https://example.org/b)"),
    ("[home]\\(README.md)", "[home]\\(README.md)"),
])
def test_a_twin_resolves_each_link_shape_markdown_reads_and_no_other(source: str,
                                                                    want: str) -> None:
    assert _twin(source) == want


def test_a_destination_with_parentheses_is_one_destination() -> None:
    out = _twin("[x](REFERENCE_(1).md)", ("README.md", "REFERENCE_(1).md"))
    assert out == "[x](https://github.com/scry-mcp/scry-mame/blob/main/REFERENCE_%281%29.md)"


def test_a_twin_that_cannot_account_for_every_link_markdown_reads_is_invalid() -> None:
    with pytest.raises(Invalid, match=r"mame/README.md.*destinations"):
        _twin("> [home](README.md)\n>\n> [h]: README.md\n")


def test_a_link_markdown_reads_that_the_scan_missed_is_invalid_even_with_a_definition() -> None:
    with pytest.raises(Invalid, match=r"mame/README.md.*destinations"):
        _twin("[x]()\n\n[h]: README.md\n")


def test_an_empty_destination_is_invalid_and_names_what_differs() -> None:
    with pytest.raises(Invalid, match=r"destinations markdown reads.*''"):
        _twin("[x]()\n")


def test_a_definition_an_image_uses_resolves_as_an_image() -> None:
    assert _twin("![x][img]\n\n[img]: screen.png\n") == "![x][img]\n\n[img]: screen.png\n"
    assert _twin("![img]\n\n[img]: screen.png\n") == "![img]\n\n[img]: screen.png\n"
    assert _twin("[x][img]\n\n[img]: screen.png\n").endswith(
        "[img]: https://github.com/scry-mcp/scry-mame/blob/main/screen.png\n")


def test_an_indented_line_after_a_definition_is_code_and_is_no_missed_link() -> None:
    src = "[h]: README.md\n    [home](README.md)\n"
    assert _twin(src) == "[h]: index.md\n    [home](README.md)\n"


def test_a_reference_use_resolves_through_its_definition_only() -> None:
    assert _twin("[a][h]\n\n[h]: README.md\n") == "[a][h]\n\n[h]: index.md\n"


@pytest.mark.parametrize("eol", ["\r\n", "\r"])
def test_a_twin_reads_a_page_with_dos_or_old_mac_line_ends(eol: str) -> None:
    src = eol.join(["```", "[home](README.md)", "```", "[home](README.md)", ""])
    assert _twin(src) == eol.join(["```", "[home](README.md)", "```", "[home](index.md)", ""])


def test_check_names_a_missing_file_and_a_missing_id(tmp_path: Path) -> None:
    (tmp_path / "a.html").write_text('<h2 id="here">x</h2><a href="#here">ok</a>'
                                     '<a href="b.html#gone">x</a><img src="pic.png">'
                                     '<a href="https://example.org/">out</a>')
    (tmp_path / "b.html").write_text('<p id="there">y</p>')
    with pytest.raises(Invalid) as e:
        check(tmp_path)
    assert "a.html: b.html#gone (no id 'gone')" in str(e.value)
    assert "a.html: pic.png (no file)" in str(e.value)


def test_check_refuses_a_link_whose_case_differs_from_the_file(tmp_path: Path) -> None:
    (tmp_path / "a.html").write_text('<a href="Guide.html">x</a><img src="Pic.PNG">')
    (tmp_path / "guide.html").write_text("<p>y</p>")
    (tmp_path / "pic.png").write_bytes(b"\x89PNG")
    with pytest.raises(Invalid) as e:
        check(tmp_path)
    assert "a.html: Guide.html (no file)" in str(e.value)
    assert "a.html: Pic.PNG (no file)" in str(e.value)


@pytest.mark.parametrize("attr", ["poster", "srcset"])
def test_check_follows_a_poster_and_a_srcset_the_way_it_follows_a_src(tmp_path: Path,
                                                                      attr: str) -> None:
    (tmp_path / "a.html").write_text(f'<img {attr}="gone.png" src="clip.webp">')
    (tmp_path / "clip.webp").write_bytes(b"RIFF")
    with pytest.raises(Invalid, match=r"a.html: gone.png \(no file\)"):
        check(tmp_path)


def test_check_examining_nothing_is_invalid(tmp_path: Path) -> None:
    with pytest.raises(Invalid, match="no page"):
        check(tmp_path)
    (tmp_path / "a.html").write_text('<a href="https://example.org/">out</a>')
    with pytest.raises(Invalid, match="no internal link examined"):
        check(tmp_path)


def test_check_refuses_a_link_out_of_the_site(tmp_path: Path) -> None:
    (tmp_path / "a.html").write_text("<a href='../outside.html'>x</a><a href=\"/etc/hosts\">y</a>")
    (tmp_path.parent / "outside.html").write_text("")
    with pytest.raises(Invalid) as e:
        check(tmp_path)
    assert "a.html: ../outside.html (outside the site)" in str(e.value)
    assert "a.html: /etc/hosts (outside the site)" in str(e.value)


def test_the_not_found_page_links_from_the_site_root_so_it_works_at_any_address(
        repos: Path, tmp_path: Path) -> None:
    page = built(repos, tmp_path, "404.html")
    assert "<h1>Page not found</h1>" in page
    assert 'href="/site.css"' in page and 'href="/index.html#install"' in page
    assert 'href="#top"' in page and 'href="#content"' in page
    assert not re.search(r"""(?:href|src)="(?!/|#|https://)""", page)


def test_check_follows_the_not_found_page_s_links_from_the_site_root(tmp_path: Path) -> None:
    (tmp_path / "404.html").write_text('<a href="/a.html#here">ok</a><a href="/gone.html">x</a>'
                                       '<a href="/../up.html">y</a><a href="/#nope">w</a>')
    (tmp_path / "a.html").write_text('<p id="here"></p><a href="/404.html">z</a>')
    with pytest.raises(Invalid) as e:
        check(tmp_path)
    assert "404.html: /gone.html (no file)" in str(e.value)
    assert "404.html: /../up.html (outside the site)" in str(e.value)
    assert "404.html: /#nope (no file)" in str(e.value)
    assert "a.html: /404.html (outside the site)" in str(e.value)
    assert "/a.html#here" not in str(e.value)


def test_check_refuses_an_id_a_page_holds_twice(tmp_path: Path) -> None:
    (tmp_path / "a.html").write_text('<h2 id="pages">Pages</h2><nav id="pages"></nav>'
                                     '<a href="a.html#pages">x</a>')
    with pytest.raises(Invalid, match=r"a.html.*'pages'.*twice"):
        check(tmp_path)


# ---- search engines and measurement ---------------------------------------------------------

GA_ID = "G-TESTTEST12"


def test_every_page_names_its_own_address_and_the_not_found_page_stays_out_of_every_index(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    for page in ("index.html", "mame/index.html", "mame/reference/breakpoints/watch_add.html",
                 "mame/demos/gridlee/index.html", "privacy.html"):
        text = (site / page).read_text()
        want = "https://scryai.net/" if page == "index.html" else f"https://scryai.net/{page}"
        assert text.count('<link rel="canonical"') == 1, page
        assert f'<link rel="canonical" href="{want}">' in text, page
        assert f'<meta property="og:url" content="{want}">' in text, page
        assert "noindex" not in text, page
    missing = (site / "404.html").read_text()
    assert '<meta name="robots" content="noindex">' in missing
    assert "canonical" not in missing


def test_only_the_home_carries_the_structured_data(repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    home = (site / "index.html").read_text()
    found = re.search(r'<script type="application/ld\+json">(.*?)</script>', home)
    assert found
    data = json.loads(found[1])
    assert data["@type"] == "SoftwareApplication"
    assert data["url"] == "https://scryai.net/"
    assert data["description"] == build.TAGLINE
    assert "ld+json" not in (site / "mame/index.html").read_text()


def test_the_sitemap_lists_every_built_page_but_the_not_found_one(repos: Path,
                                                                  tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    listed = set(re.findall(r"<loc>(.*?)</loc>", (site / "sitemap.xml").read_text()))
    built_pages = {p.relative_to(site).as_posix() for p in site.rglob("*.html")} - {"404.html"}
    want = {"https://scryai.net/" if p == "index.html" else f"https://scryai.net/{p}"
            for p in built_pages}
    assert len(want) > 20
    assert listed == want


def test_robots_invites_the_ai_crawlers_by_name_and_points_at_the_sitemap(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    robots = (tmp_path / "site" / "robots.txt").read_text()
    for name in ("GPTBot", "OAI-SearchBot", "ClaudeBot", "PerplexityBot", "Google-Extended"):
        assert f"User-agent: {name}\nAllow: /\n" in robots
    assert "Disallow" not in robots
    assert robots.endswith("Sitemap: https://scryai.net/sitemap.xml\n")


def test_the_site_serves_the_indexnow_key_and_the_sitemap_does_not_list_it(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    key = seo.INDEXNOW_KEY
    assert re.fullmatch(r"[0-9a-f]{32}", key)
    assert (site / f"{key}.txt").read_text() == key
    assert key not in (site / "sitemap.xml").read_text()


def test_the_machine_s_property_id_never_reaches_a_build() -> None:
    assert "SCRY_GA4_ID" not in os.environ


def test_a_build_without_a_property_id_has_no_banner_and_no_tag(
        repos: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SCRY_GA4_ID", raising=False)
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    for page in ("index.html", "cookies.html", "mame/index.html", "404.html"):
        text = (site / page).read_text()
        assert 'id="consent"' not in text and "consent.js" not in text, page
    assert 'href="privacy.html"' in (site / "cookies.html").read_text()


def test_a_build_with_a_property_id_shows_the_banner_closed_and_loads_only_the_script_file(
        repos: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCRY_GA4_ID", GA_ID)
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    page = (site / "mame/reference/breakpoints/watch_add.html").read_text()
    assert re.search(r'<section class="consent" id="consent"[^>]* hidden>', page)
    assert (f'<script defer src="../../../consent.js" data-ga="{GA_ID}" '
            'data-host="scryai.net">') in page
    assert page.count("Reject") == 1 and page.count(">Accept<") == 1
    assert "googletagmanager" not in page
    assert "googletagmanager" in (site / "consent.js").read_text()
    # the not-found page is served at any depth, so it reaches the script from the root
    assert 'src="/consent.js"' in (site / "404.html").read_text()


@pytest.mark.parametrize("value", ["UA-12345-1", "g-abc123def4", "G-", "G-ABC 123", "x"])
def test_a_property_id_that_is_not_one_is_invalid(
        repos: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("SCRY_GA4_ID", value)
    with pytest.raises(Invalid, match="SCRY_GA4_ID"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


def test_every_page_links_the_privacy_and_cookies_pages_and_they_link_each_other(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    assert 'href="./privacy.html">Privacy' in (site / "index.html").read_text()
    assert 'href="../../../privacy.html">Privacy' in (
        site / "mame/demos/gridlee/index.html").read_text()
    assert 'href="privacy.html"' in (site / "cookies.html").read_text()
    assert 'href="cookies.html"' in (site / "privacy.html").read_text()


# ---- the knowledge base ----------------------------------------------------------------------

BASE_OF = {"scry-mame": "mame", "scry-dosbox-x": "dosbox-x"}


@pytest.mark.parametrize("name", sorted(BASE_OF))
@pytest.mark.parametrize(("change", "message"), [
    ({"kinds": ()}, "serves 0 entries with 0 faults"),
    ({"faults": 2}, "serves 3 entries with 2 faults"),
])
def test_a_base_that_serves_nothing_or_reports_faults_stops_the_build(
        repos: Path, tmp_path: Path, name: str, change: dict[str, object],
        message: str) -> None:
    for rel, body in base_files(BASE_OF[name], **change).items():  # type: ignore[arg-type]
        track(repos / name, rel, body)
    with pytest.raises(Invalid, match=rf"{name}: its knowledge base {message}"):
        build.build(repos, tmp_path / "site")
    assert not (tmp_path / "site").exists()


@pytest.mark.parametrize("name", sorted(BASE_OF))
def test_a_base_that_does_not_load_stops_the_build(repos: Path, tmp_path: Path,
                                                   name: str) -> None:
    for rel in base_files(BASE_OF[name]):
        if rel.endswith(("knowledge.py", "support.py")):
            track(repos / name, rel, "raise RuntimeError('the base is broken')\n")
    with pytest.raises(Invalid, match=rf"{name}: its knowledge base did not load.*broken"):
        build.build(repos, tmp_path / "site")


def test_the_knowledge_base_is_a_page_and_a_section_called_what_it_is(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    page = (site / "knowledge/index.html").read_text()
    home = (site / "index.html").read_text()
    assert "<h1>Knowledge base</h1>" in page
    assert '<h2>The knowledge base</h2>' in home
    assert 'href="knowledge/index.html">Knowledge base</a>' in home
    assert '<a href="../reference/index.html" aria-current=page>Reference' in page
    for text in (page, home, (site / "reference/index.html").read_text()):
        assert "Names for numbers" not in text and "Numbers come with" not in text


def test_no_page_counts_the_base_or_says_what_it_holds_back(
        repos: Path, tmp_path: Path) -> None:
    for rel, body in base_files("dosbox-x", kinds=(("call", "rbil61"),) * 7,
                                held_back=11).items():
        track(repos / "scry-dosbox-x", rel, body)
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    home = (site / "index.html").read_text()
    pages = home + (site / "knowledge/index.html").read_text() + (
        site / "reference/index.html").read_text()
    for gone in ("<b>7</b>", "entries for", ">7 entries<", ">11<"):
        assert gone not in pages, gone
    for words in ("held back", "held_back", "held-back", "until checked", "not complete",
                  "second reader"):
        assert words not in pages, words
    seen = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(
        r"<(style|script)\b.*?</\1>", "", pages, flags=re.S)))
    assert not re.search(r"\b11\b", seen)


def test_the_home_names_the_server_of_its_example(repos: Path, tmp_path: Path) -> None:
    for rel, body in base_files("mame", kinds=(("register", "datasheet"),) * 9).items():
        track(repos / "scry-mame", rel, body)
    home = built(repos, tmp_path, "index.html")
    example = home[home.index('<section id="knowledge">'):home.index('<section id="emulators">')]
    assert "for MAME" in example


def test_the_example_shows_the_entry_and_not_the_bookkeeping(repos: Path,
                                                             tmp_path: Path) -> None:
    home = built(repos, tmp_path, "index.html")
    section = home[home.index('<section id="knowledge">'):home.index('<section id="emulators">')]
    shown = section.split("<details")[0]
    assert "2 of 4 fields" in shown
    assert "Ends the program with return code AL." in shown
    assert "as the source comment says real MS-DOS" not in shown and "…" in shown
    assert "entries_total" not in shown
    assert "entries_total" in section
    words = html.unescape(re.sub(r"<[^>]+>", "", section))
    assert "held_back" not in words and '"served"' not in words and "served" not in words.split()


def test_the_whole_reply_is_a_closed_details_nothing_of_it_cut(
        repos: Path, tmp_path: Path) -> None:
    page = built(repos, tmp_path, "knowledge/index.html")
    assert '<details class="whole" open' not in page
    start = page.index('<details class="whole">')
    whole = page[start:page.index("</details>", start)]
    assert "…" not in whole
    assert "as the source comment says real MS-DOS" in whole
    assert "served" not in whole and "held_back" not in whole
    pane = page[page.index('<div class="pane-h">Reply'):start]
    shown = pane[pane.index("<pre><code>") + len("<pre><code>"):pane.index("</code></pre>")]
    assert len(html.unescape(re.sub(r"<[^>]+>", "", shown)).splitlines()) <= 12


@pytest.mark.parametrize("reads", [
    "One entry matches. served and held_back count what the base holds.",
    "One entry matches. `held_back` counts what the base holds.",
])
def test_a_reading_sentence_that_names_the_counts_is_left_out_with_or_without_quotes(
        repos: Path, tmp_path: Path, reads: str) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    replace(f, "One entry matches, so `entries` answers it whole. "
            "`served` and `held_back` count what the base serves and holds back.", reads)
    page = built(repos, tmp_path, "knowledge/index.html")
    assert "One entry matches." in page and "held_back" not in page


def test_an_example_whose_only_reading_sentence_counts_what_the_base_holds_stops_the_build(
        repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    replace(f, "One entry matches, so `entries` answers it whole. "
            "`served` and `held_back` count what the base serves and holds back.",
            "`served` and `held_back` count what the base holds.")
    with pytest.raises(Invalid, match=r"names.md, knowledge_find: .*reading sentence"):
        build.build(repos, tmp_path / "site")


def test_the_page_says_how_its_entries_are_checked_and_what_a_number_without_one_stays(
        repos: Path, tmp_path: Path) -> None:
    page = built(repos, tmp_path, "knowledge/index.html")
    assert "checked against the source it cites" in page
    assert "a number the base has no entry for stays a number" in page


@pytest.mark.parametrize("whole", [
    '{"summary": "x", "entries": []}',
    '{"summary": "x", "entries": [{"name": "a"}, {"name": "b"}]}',
    '{"summary": "x", "entries": [{"key": "a"}]}',
    "not json",
])
def test_an_example_whose_reply_is_not_a_single_named_entry_stops_the_build(
        repos: Path, tmp_path: Path, whole: str) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    replace(f, "```json\n" + FOUND + "\n```", f"```json\n{whole}\n```")
    with pytest.raises(Invalid, match=r"scry-mame/docs/reference/names.md, knowledge_find: .*"
                                      "single named entry"):
        build.build(repos, tmp_path / "site")


def test_a_server_citing_the_other_emulators_source_says_why(repos: Path,
                                                             tmp_path: Path) -> None:
    page = built(repos, tmp_path, "knowledge/index.html")
    mame, dosbox = page.split('<section><h2 id="dosbox-x">')[0], page.split(
        '<section><h2 id="dosbox-x">')[1]
    assert "the chips both emulators share, so they cite DOSBox-X's source" in mame
    assert "both emulators share" not in dosbox
    assert "Ralf Brown&#x27;s Interrupt List</a>" in page and "release 61" not in page


def test_llms_txt_lists_the_knowledge_base_page_and_the_reference_links_its_section(
        repos: Path, tmp_path: Path) -> None:
    build.build(repos, tmp_path / "site")
    site = tmp_path / "site"
    assert "- [Knowledge base](knowledge/index.html): " in (site / "llms.txt").read_text()
    assert 'href="../mame/reference/index.html#knowledge-base"' in (
        site / "knowledge/index.html").read_text()


def test_a_server_without_the_tools_the_page_links_stops_the_build_with_a_message(
        repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    f.write_text(f.read_text().replace("knowledge_find", "knowledge_seek"))
    replace(repos / "scry-mame/REFERENCE.md", "knowledge_find", "knowledge_seek")
    with pytest.raises(Invalid, match="scry-mame"):
        build.build(repos, tmp_path / "site")


def test_a_base_that_prints_or_imports_what_the_checkouts_do_not_hold_stops_the_build(
        repos: Path, tmp_path: Path) -> None:
    track(repos / "scry-mame", "src/scry_mame/knowledge/support.py",
          "print('noise')\n" + base_files("mame")["src/scry_mame/knowledge/support.py"])  # type: ignore[operator]
    with pytest.raises(Invalid, match="scry-mame: its knowledge base .*answer"):
        build.build(repos, tmp_path / "site")
    track(repos / "scry-mame", "src/scry_mame/knowledge/support.py",
          "import pytest\n" + base_files("mame")["src/scry_mame/knowledge/support.py"])  # type: ignore[operator]
    with pytest.raises(Invalid, match="scry-mame: its knowledge base did not load.*pytest"):
        build.build(repos, tmp_path / "site")


def test_a_base_citing_an_emulator_with_a_pin_links_that_emulators_tree_at_the_pin(
        repos: Path, tmp_path: Path) -> None:
    for rel, body in base_files("dosbox-x", kinds=(("call", "mame"),)).items():
        track(repos / "scry-dosbox-x", rel, body)
    page = built(repos, tmp_path, "knowledge/index.html")
    assert 'href="https://github.com/mamedev/mame/tree/mame0289"' in page


def test_an_example_of_two_calls_is_refused_where_the_knowledge_base_shows_it(
        repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    entry_text = entry("knowledge_find", whole=FOUND, second=True, reads="One entry matches.")
    text = f.read_text()
    start = text.index("<!-- scry-reference:begin knowledge_find -->")
    end = text.index("<!-- scry-reference:end knowledge_find -->")
    f.write_text(text[:start] + entry_text.split("<!-- scry-reference:end")[0]
                 + text[end:])
    with pytest.raises(Invalid, match=r"names.md, knowledge_find: .*has one call"):
        build.build(repos, tmp_path / "site")


def test_a_link_to_a_heading_of_the_family_inside_the_example_lands_on_the_family_page(
        repos: Path, tmp_path: Path) -> None:
    f = repos / "scry-mame/docs/reference/names.md"
    replace(f, "One entry matches, so `entries` answers it whole.",
            "One entry matches. See [the states](#what-each-state-means).")
    page = built(repos, tmp_path, "knowledge/index.html")
    assert 'href="../mame/reference/names/index.html#what-each-state-means"' in page
