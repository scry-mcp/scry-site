"""Build the SCRY site from checkouts of scry-core, scry-mame and scry-dosbox-x.

Prints one JSON line (pages, copied files, internal links followed) and exits 0; or writes
nothing, prints INVALID with the reason, and exits 3.
"""

from __future__ import annotations

import argparse
import dataclasses
import html
import json
import os
import posixpath
import re
import shutil
import sys
import tempfile
from collections.abc import Callable
from importlib import resources
from pathlib import Path

from scry_site import (
    analytics,
    demos,
    example,
    home,
    knowledge,
    motion,
    reference,
    render,
    seo,
    sources,
)
from scry_site.check import NOT_FOUND, check
from scry_site.sources import GROUPS, Family, Invalid, Page, Repo, collect, read, repos

TAGLINE = "MCP servers that hold MAME or DOSBox-X open so your AI client can debug the program " \
          "inside."
_KEY = re.compile(r"\{\{([a-z_]+)\}\}")


def template(name: str, **fill: str) -> str:
    """Fill every `{{key}}` in one pass, so a key that appears inside a value stays as text."""
    text = resources.files("scry_site").joinpath("templates", name).read_text(encoding="utf-8")
    return _KEY.sub(lambda m: fill[m[1]], text)


def credits_line(core: Repo) -> str:
    """The credits line every SCRY README closes with, rendered once for every page's footer."""
    body = sources.section(read(core, "README.md"), "Credits", "scry-core/README.md").strip()
    if "\n" in body or not body.startswith("Developed by Optimiza"):
        raise Invalid("scry-core/README.md: '## Credits' must hold one line, starting "
                      f"'Developed by Optimiza'; it holds: {body[:80]!r}")
    return inline(body)


def inline(md: str) -> str:
    return render.markdown(md).strip().removeprefix("<p>").removesuffix("</p>")


def describe(page: Page) -> str:
    """The page's first paragraph as one line of at most 200 characters, else its title."""
    md, hidden = page.markdown, sources.masked(page.markdown)
    for m in re.finditer(r"(?:^[^\n]*\S[^\n]*(?:\n|\Z))+", hidden, re.M):
        block = md[m.start():m.end()]
        if block[0].isalpha() or block[0] in "`_" or re.match(r"\*\S", block):
            text = render.plain(block)
            if not text:
                continue
            return short(text)
    return page.title


def short(text: str) -> str:
    if len(text) <= 200:
        return text
    return text[:200].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def llms_txt(rs: list[Repo], pages: list[Page]) -> str:
    """The pages that have a markdown twin, by repository and group, then the knowledge base's page,
    which is built whole and has none, as llmstxt.org lays out."""
    lines = ["# SCRY", "", f"> {TAGLINE}", ""]
    order = {g: i for i, (g, _) in enumerate((*GROUPS, ("core", "")))}
    for r in rs:
        ps = sorted((p for p in pages if p.repo is r), key=lambda p: (order[p.group], p.order))
        lines += [f"## {r.label}", ""]
        lines += [f"- [{p.title}]({twin_path(p)}): {describe(p)}" for p in ps]
        lines.append("")
    lines += ["## Site", "", f"- [{knowledge.TITLE}]({knowledge.OUT}): {knowledge.DESCRIPTION}", ""]
    return "\n".join(lines)


def twin_path(page: Page) -> str:
    return page.out.removesuffix(".html") + ".md"


def rel(target: str, out: str) -> str:
    return posixpath.relpath(target, posixpath.dirname(out) or ".")


def crumbs(out: str, trail: list[tuple[str, str]], twin: tuple[str, str] | None = None) -> str:
    """`SCRY / ... / here`: each step but the last a link; then, where the other server has the
    same page, a link to it."""
    steps = [f'<a href="{rel(href, out)}">{html.escape(text)}</a>' for text, href in trail[:-1]]
    steps.append(f"<span>{html.escape(trail[-1][0])}</span>")
    also = (f'<a class="twin" href="{rel(twin[1], out)}">Also in {html.escape(twin[0])}</a>'
            if twin else "")
    return f'<p class="crumbs">{"<span aria-hidden=true>/</span>".join(steps)}{also}</p>'


#: A row: its text, its page, its `aria-current` value ("" for none) and its nested sections.
Item = tuple[str, str, str, list[tuple[str, str]]]


def side(title: str, about: str, summary: str, groups: list[tuple[str, list[Item]]], kind: str,
         out: str, head: str = "") -> str:
    """The side list: closed above the page on a phone, open beside it on a desktop. The page
    that is open carries its own sections nested under it. `head` opens it, on a desktop above
    the list's own scroll."""
    blocks = []
    for name, items in groups:
        rows = []
        for text, href, current, subs in items:
            here = f" aria-current={current}" if current else ""
            nested = "".join(f'<li><a href="#{i}">{html.escape(t)}</a></li>' for i, t in subs)
            rows.append(f'<li><a{here} href="{rel(href, out)}">{html.escape(text)}</a>'
                        f'{f"<ul class=sub>{nested}</ul>" if nested else ""}</li>')
        grp = f'<p class="grp">{html.escape(name)}</p>' if name else ""
        blocks.append(f'{grp}<ul>{"".join(rows)}</ul>')
    lists = "".join(blocks)
    note = f'<p class="about">{about}</p>' if about else ""
    top = f'<div class="side-top">{head}</div>' if head else ""
    return (f'<nav class="side {kind}" id="side-list" aria-label="{html.escape(title)}">'
            f'<details class="side-m"><summary>{html.escape(summary)}</summary>{head}{note}{lists}'
            f'</details>{top}'
            f'<div class="side-d"><p>{html.escape(title)}</p>{note}{lists}</div></nav>')


def doc_side(pages: list[Page], current: Page, subs: list[tuple[str, str]]) -> str:
    """The side list of a repository's documents: its README, reference, demos, contributing."""
    groups = []
    named = (*GROUPS, ("core", ""))
    for group, label in named:
        ps = sorted((p for p in pages if p.repo is current.repo and p.group == group),
                    key=lambda p: p.order)
        if ps:
            groups.append((label, [(p.label, p.out, "page" if p is current else "",
                                    subs if p is current else []) for p in ps]))
    count = sum(len(items) for _, items in groups)
    return side(current.repo.label, "", f"{current.repo.label}: {count} pages", groups, "docs",
                current.out)


def tool_side(f: Family, fams: list[Family], ts: list[reference.Tool], current: str, out: str,
              subs: list[tuple[str, str]]) -> str:
    """The side list of a family: the way up to its server's reference, its sentence, its tools
    (the open one with its sections), then every family of the server."""
    server = f.page.repo
    head = (f'<a class="up" href="{rel(f"{server.key}/reference/index.html", out)}">'
            f'<span aria-hidden="true">&#9664;</span> {html.escape(server.label)} reference</a>')
    items: list[Item] = [(t.name, t.out, "page" if t.name == current else "",
                          subs if t.name == current else []) for t in ts]
    top: list[Item] = [(f"About {f.page.label}", f.page.out, "" if current else "page",
                        [] if current else subs)]
    others: list[Item] = [(g.page.label, g.page.out, "true" if g is f else "", []) for g in fams]
    return side(f.page.label, inline(f.about), f"{f.page.label}: {len(ts)} tools",
                [("", top), ("Tools", items), ("Families", others)], "tools", out, head)


def shell(*, title: str, description: str, out: str, body: str, credits: str, head: str = "",
          nav: str = "", measurement: str = "") -> str:
    # The not-found page is served at whatever address was asked, so it links from the root.
    root = "" if out == NOT_FOUND else rel(".", out) if posixpath.dirname(out) else "."
    on = {k: " aria-current=page" if nav == k else "" for k in ("demos", "reference")}
    return template("page.html", title=html.escape(title), description=html.escape(description),
                    root=root, head=f"<style>\n{head}\n</style>" if head else "", body=body,
                    credits=credits, nav_demos=on["demos"], nav_reference=on["reference"],
                    seo=seo.head(out, title, description, TAGLINE),
                    consent=analytics.banner(root, measurement),
                    tracking=analytics.script(root, measurement))


#: A command page's way back to its side list, for a reader deep in the text on a phone.
BACK = '<a class="tolist" href="#side-list"><span aria-hidden="true">&#9650;</span> Tools</a>'


def framed(side_html: str, main: str) -> str:
    return (f'<div class="wrap docframe">{side_html}<main id="content" class="doc">{main}</main>'
            "</div>")


def solo(main: str) -> str:
    return f'<main id="content" class="wrap doc solo">{main}</main>'


def guard(base: Path, out: Path) -> None:
    """`out` is replaced whole, so it may not hold the sources, nor be anything but an earlier
    build or an empty directory."""
    if out.exists() and not out.is_dir():
        raise Invalid(f"--out {out} is not a directory")
    if out.is_dir() and any(out.iterdir()) and not (out / ".nojekyll").exists():
        raise Invalid(f"--out {out} holds files no build made; replacing it would delete them")
    if out == base or out in base.parents:
        raise Invalid(f"--out {out} is or holds {base}, where the checkouts are; replacing it "
                      "would delete them")
    for r in repos(base):
        if out == r.root or r.root in out.parents:
            raise Invalid(f"--out {out} is inside the {r.name} checkout")


class Site:
    """One build: the sources read, the pages rendered, the files to copy."""

    def __init__(self, rs: list[Repo]) -> None:
        self.rs = rs
        self.pages, self.families, self.files = collect(rs)
        self.links = render.Links({(p.repo.key, p.src): p.out for p in self.pages}, self.files)
        self.tools: dict[str, list[reference.Tool]] = {}
        self.tool_pages: dict[tuple[str, str], str] = {}
        for f in self.families:
            ts = reference.tools(f)
            self.tools[f.page.out] = ts
            self.links.anchors.update(reference.anchors(f, ts))
            for t in ts:
                key = (f.page.repo.key, t.name)
                if key in self.tool_pages:
                    raise Invalid(f"{f.page.repo.name}: two entries of `{t.name}`")
                self.tool_pages[key] = t.out
        self.credits = credits_line(self.repo("core"))
        self.measurement = analytics.measurement_id(os.environ)
        self.rendered: dict[str, str] = {}
        self.served = [knowledge.read(self.repo("core"), r) for r in rs if r.key != "core"]
        self.clips: dict[str, motion.Clip] = {}

    def repo(self, key: str) -> Repo:
        return next(r for r in self.rs if r.key == key)

    def label(self, key: str) -> str:
        return self.repo(key).label

    def writers(self, page: Page, *, virtual: bool = False) -> tuple[Callable[[str], str],
                                                                      Callable[[str], str]]:
        """Inline and block markdown, rendered for `page` with its links resolved."""
        def one(md: str) -> str:
            return render.rewrite(inline(md), page, self.links, virtual=virtual)

        def many(md: str) -> str:
            return render.rewrite(render.markdown(md), page, self.links, virtual=virtual)
        return one, many

    def linked(self, key: str, name: str) -> str:
        """The page of tool `name` of server `key`, which the knowledge base page links."""
        try:
            return self.tool_pages[(key, name)]
        except KeyError:
            raise Invalid(f"{self.repo(key).name}: no entry of `{name}` in its reference, which "
                          "the knowledge base page links") from None

    def asked(self, key: str, out: str, *, tagged: bool = False) -> str:
        """`knowledge_find`'s example of the server `key`, drawn for the page at `out`; headed
        by where it can be tried, or `tagged` by its server where the page is no server's."""
        t = next((t for ts in self.tools.values() for t in ts
                  if t.name == "knowledge_find" and t.family.page.repo.key == key), None)
        if t is None:
            raise Invalid(f"{self.repo(key).name}: no entry of `knowledge_find` in its reference")
        f = t.family.page
        where = f"{f.repo.name}/{f.src}, knowledge_find"
        one, many = self.writers(Page(f.repo, f.src, out, "reference", t.markdown), virtual=True)
        ex = example.parse(dict(t.sections)["Try it"], where, located=True)
        if len(ex.calls) != 1:
            raise Invalid(f"{where}: the example the knowledge base is shown by has one call")
        reply, fields = knowledge.excerpt(ex.whole, where)
        ex = dataclasses.replace(ex, calls=tuple(
            dataclasses.replace(c, fields=fields, reply=reply) for c in ex.calls))
        tag = "mame" if key == "mame" else "dos"
        caption = (f'<span class="tag {tag}">{html.escape(f.repo.label)}</span>' if tagged
                   else one(ex.where))
        return example.render(ex, caption=caption, inline=one, block=many)

    def clip(self, page: Page) -> motion.Clip:
        src = posixpath.join(posixpath.dirname(page.src), motion.LOOP)
        if src not in self.files[page.repo.key]:
            raise Invalid(f"{page.repo.name}: {src} is not tracked, and every demo is shown moving")
        if page.out not in self.clips:
            self.clips[page.out] = motion.clip(page.repo.root / src, f"{page.repo.name}/{src}")
        return self.clips[page.out]

    def put(self, page_out: str, title: str, description: str, body: str, *, head: str = "",
            nav: str = "") -> None:
        self.rendered[page_out] = shell(title=title, description=description, out=page_out,
                                        body=body, credits=self.credits, head=head, nav=nav,
                                        measurement=self.measurement)

    def demo_list(self) -> list[home.Demo]:
        """Every demo once, by name: the hero's first, then each front door's order."""
        said = {r.key: sources.demo_sentences(read(r, "README.md"), f"{r.name}/README.md")
                for r in self.rs if r.key != "core"}
        hero_demo = sources.lead(read(self.repo(home.HERO), "README.md"),
                                 f"{self.repo(home.HERO).name}/README.md").demo
        server_order = {k: i for i, (k, _, _) in enumerate(sources.SERVERS)}

        def folder(p: Page) -> str:
            return posixpath.basename(posixpath.dirname(p.src))
        by_name: dict[str, list[Page]] = {}
        for p in sorted((p for p in self.pages if p.group == "demos"),
                        key=lambda p: (folder(p) != hero_demo, server_order[p.repo.key], p.order)):
            by_name.setdefault(folder(p), []).append(p)
        found = []
        for name, ps in by_name.items():
            first = ps[0]
            says = said[first.repo.key].get(name)
            if says is None:
                raise Invalid(f"{first.repo.name}/README.md: 'See it run' does not list "
                              f"demos/{name}/")
            text = inline(says)
            text = text[:1].upper() + text[1:]
            found.append(home.Demo(name, first.label, text, tuple(ps), self.clip(first)))
        return found

    def render_pages(self, ds: list[home.Demo]) -> None:
        for p in self.pages:
            if p.group == "demos":
                self.demo_page(p, ds)
            elif p.out in self.tools:
                self.family_pages(next(f for f in self.families if f.page is p))
            else:
                one, many = self.writers(p)
                body = many(p.markdown)
                self.put(p.out, f"{p.title} · SCRY", describe(p),
                         framed(doc_side(self.pages, p, render.sections(body)), body))

    def family_pages(self, f: Family) -> None:
        p = f.page
        server = self.label(p.repo.key)
        ts = self.tools[p.out]
        fams = [g for g in self.families if g.page.repo is p.repo]
        other = next(r for r in self.rs if r.key not in ("core", p.repo.key))
        one, many = self.writers(p, virtual=True)
        own = many(reference.without_entries(p.markdown))
        trail = [("SCRY", "index.html"), (server, f"{p.repo.key}/index.html"),
                 ("Reference", f"{p.repo.key}/reference/index.html")]

        def twin(out: str | None) -> tuple[str, str] | None:
            """The same page on the other server, where it has one."""
            return (other.label, out) if out else None
        same = p.out.replace(f"{p.repo.key}/", f"{other.key}/", 1)
        has = same in (g.page.out for g in self.families)
        body = reference.family_main(
            f, ts, own, crumbs(p.out, [*trail, (p.label, p.out)], twin(same if has else None)),
            one)
        self.put(p.out, f"{p.label} · SCRY for {server}", describe(p),
                 framed(tool_side(f, fams, ts, "", p.out, render.sections(body)), body),
                 nav="reference")
        for t in ts:
            tp = t.page
            one, many = self.writers(tp, virtual=True)
            body = reference.main(t, server=server, server_key=p.repo.key,
                                  crumbs=crumbs(t.out, [*trail, (p.label, p.out), (t.name, t.out)],
                                                twin(self.tool_pages.get((other.key, t.name)))),
                                  inline=one, block=many)
            subs = [(reference.slug(title), title) for title, _ in t.sections]
            self.put(t.out, f"{t.name} · SCRY for {server}", render.plain(t.what),
                     framed(tool_side(f, fams, ts, t.name, t.out, subs), body + BACK),
                     nav="reference")

    def demo_page(self, p: Page, ds: list[home.Demo]) -> None:
        server = self.label(p.repo.key)
        where = f"{p.repo.name}/{p.src}"
        one, many = self.writers(p)
        here = posixpath.dirname(p.out)
        cards = []
        for d in ds:
            if p in d.pages or all(q.repo is not p.repo for q in d.pages):
                continue
            # this server's other demos, each card leading to this server's page of it
            mine = tuple(sorted(d.pages, key=lambda q: q.repo is not p.repo))
            cards.append(home.card(dataclasses.replace(d, pages=mine, clip=self.clip(mine[0])),
                                   here))
        more = "".join(cards)
        trail = [("SCRY", "index.html"), (server, f"{p.repo.key}/index.html"),
                 ("Demos", "index.html#demos"), (p.label, p.out)]
        body, keys = demos.main(p, sources.motion(p.markdown, where), self.clip(p), server=server,
                                crumbs=crumbs(p.out, trail), more=more, inline=one, block=many)
        self.put(p.out, f"{p.label} · SCRY for {server}", describe(p), solo(body), head=keys,
                 nav="demos")

    def reference_index(self) -> None:
        """One page listing both servers' families: where the bar's Reference leads."""
        out = "reference/index.html"
        cols = []
        for r in self.rs:
            if r.key == "core":
                continue
            fams = [f for f in self.families if f.page.repo is r]
            rows = "".join(f'<li><a href="{rel(f.page.out, out)}">{html.escape(f.page.label)}</a>'
                           f"<span>{inline(f.about)}</span></li>" for f in fams)
            n = sum(len(self.tools[f.page.out]) for f in fams)
            cols.append(f'<section><h2 id="{r.key}">{html.escape(r.label)}</h2>'
                        f'<p class="muted">{n} tools in {len(fams)} families. '
                        f'<a href="{rel(f"{r.key}/reference/index.html", out)}">The rules the '
                        f'{html.escape(r.label)} tools share</a>.</p>'
                        f'<ul class="toollist fams">{rows}</ul></section>')
        body = (crumbs(out, [("SCRY", "index.html"), ("Reference", out)])
                + "<h1>Reference</h1><p class=lead>Every tool of both servers has a page, with an "
                "example you can try.</p>" + knowledge.line(self.served, rel(knowledge.OUT, out))
                + f'<div class="refcols">{"".join(cols)}</div>')
        self.put(out, "Reference · SCRY", "Every tool of the two SCRY servers, by family.",
                 solo(body), nav="reference")

    def names(self) -> None:
        """The page of what the servers name and what their bases serve, under the reference."""
        out = knowledge.OUT
        cols = []
        for s in self.served:
            key = s.repo.key
            tool = self.linked(key, "knowledge_find")
            links = [("<code>knowledge_find</code>", rel(tool, out)),
                     ("The rules of the knowledge base",
                      rel(f"{key}/reference/index.html", out) + f"#{knowledge.SECTION}"),
                     ("<code>start</code>, its <code>names</code> argument",
                      rel(self.linked(key, "start"), out) + "#arguments"),
                     ("<code>disassemble</code>, a note per line",
                      rel(self.linked(key, "disassemble"), out))]
            others = [o for o in self.served if o is not s]
            cols.append(knowledge.column(s, others, self.asked(key, out), links))
        body = knowledge.page(crumbs(out, [("SCRY", "index.html"),
                                           ("Reference", "reference/index.html"),
                                           (knowledge.TITLE, out)]), cols)
        self.put(out, f"{knowledge.TITLE} · SCRY",
                 knowledge.DESCRIPTION, solo(body), nav="reference")

    def legal(self) -> None:
        """The privacy and cookies pages the foot links to."""
        self.put("privacy.html", "Privacy · SCRY", "Who runs the SCRY site and what it collects.",
                 solo(analytics.PRIVACY))
        self.put("cookies.html", "Cookies · SCRY", "The cookies the SCRY site sets, and how to "
                 "change your choice.", solo(analytics.COOKIES))

    def not_found(self) -> None:
        body = ("<h1>Page not found</h1><p class=lead>Nothing on this site lives at this "
                'address. Start from the <a href="/index.html">home</a>, the '
                '<a href="/index.html#demos">demos</a> or the '
                '<a href="/reference/index.html">reference</a>.</p>')
        self.put(NOT_FOUND, "Page not found · SCRY", "No page of the SCRY site lives at this "
                 "address.", solo(body))

    def home(self, ds: list[home.Demo]) -> None:
        servers = []
        for r in self.rs:
            if r.key == "core":
                continue
            readme_page = next(p for p in self.pages if p.repo is r and p.src == "README.md")
            md = readme_page.markdown
            where = f"{r.name}/README.md"
            at_home = Page(r, "README.md", "index.html", "overview", md)
            one, many = self.writers(at_home)
            needs, clone = sources.get_server(md, where)
            q = sources.first_question(md, where)
            demo_pages = [p for p in self.pages if p.repo is r and p.group == "demos"]
            if not demo_pages:
                raise Invalid(f"{r.name}: no demo, and the home leads to each server's demos")
            servers.append(home.Server(
                r, sources.lede(md, where), one(needs), example.pane("sh", clone.code),
                tuple((c.name, one(c.says), c.fence.language, c.fence.code)
                      for c in sources.clients(md, where)),
                (many(q.before), one(q.ask), many(q.after)),
                tuple(sources.Ask(a.question, a.tools, one(a.says))
                      for a in sources.asks(md, where)),
                f"{r.key}/reference/index.html", demo_pages[0].out))
        hero_repo = self.repo(home.HERO)
        hmd = read(hero_repo, "README.md")
        led = sources.lead(hmd, f"{hero_repo.name}/README.md")
        page = next((p for d in ds for p in d.pages
                     if d.name == led.demo and p.repo is hero_repo), None)
        if page is None:
            raise Invalid(f"{hero_repo.name}/README.md: its lead shows demos/{led.demo}/, which "
                          "has no page")
        d = next(d for d in ds if page in d.pages)
        d = dataclasses.replace(d, pages=(page,), clip=self.clip(page))
        m = sources.motion(page.markdown, f"{hero_repo.name}/{page.src}")
        fill, css = home.slots(servers, ds, self.tool_pages)
        first = max(self.served, key=lambda s: s.served)
        fill["knowledge"] = knowledge.home(
            [first, *(s for s in self.served if s is not first)],
            self.asked(first.repo.key, "index.html", tagged=True))
        body = template("landing.html", hero=home.hero(led.rows, d, led.alt, len(m.moments)),
                        **fill)
        keys = motion.keyframes(d.clip, m.ms, f"{hero_repo.name}/{d.pages[0].src}")
        self.put("index.html", "SCRY: see inside the machine", TAGLINE, body,
                 head=f"{keys}\n{css}")


def render_site(rs: list[Repo], into: Path) -> dict[str, int]:
    site = Site(rs)
    ds = site.demo_list()
    site.render_pages(ds)
    site.reference_index()
    site.names()
    site.home(ds)
    site.legal()
    site.not_found()
    twins = {twin_path(p): render.twin(p, site.links) for p in site.pages}
    if site.links.broken:
        raise Invalid("links in the sources to paths no repository tracks:\n  "
                      + "\n  ".join(sorted(site.links.broken)))
    extras = {"llms.txt": llms_txt(rs, site.pages), "robots.txt": seo.robots(),
              "sitemap.xml": seo.sitemap(site.rendered),
              f"{seo.INDEXNOW_KEY}.txt": seo.INDEXNOW_KEY}
    for path, text in {**site.rendered, **twins, **extras}.items():
        if "linkedin" in text.lower():
            raise Invalid(f"{path}: a mention of LinkedIn; the site links the author's GitHub "
                          "only, through the credits line")
        dest = into / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
    roots = {r.key: r.root for r in rs}
    media = {(p.repo.key, posixpath.join(posixpath.dirname(p.src), name)):
             posixpath.join(posixpath.dirname(p.out), name)
             for p in site.pages if p.group == "demos" for name in (motion.STILL, motion.LOOP)}
    copies = {**site.links.copies, **media}
    for (key, src), dest_rel in copies.items():
        if src not in site.files[key]:
            raise Invalid(f"{key}: {src} is not tracked, and the site shows every demo's "
                          "screen and plays its loop")
        (into / dest_rel).parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(roots[key] / src, into / dest_rel)
        except OSError as e:
            raise Invalid(f"cannot copy {key}/{src}: {e}") from e
    shutil.copytree(Path(str(resources.files("scry_site").joinpath("static"))), into,
                    dirs_exist_ok=True)
    (into / ".nojekyll").write_text("", encoding="utf-8")
    return {"pages": len(site.rendered), "copied": len(copies), "links": check(into)}


def build(base: Path, out: Path) -> dict[str, int]:
    """Render into a directory beside `out`, and put it in place only once it checks."""
    base, out = base.resolve(), out.resolve()
    rs = repos(base)
    guard(base, out)
    out.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=f".{out.name}.", dir=out.parent))
    try:
        report = render_site(rs, work)
        if out.exists():
            shutil.rmtree(out)
        work.rename(out)
    finally:
        if work.exists():
            shutil.rmtree(work)
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="scry-site", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("checkouts", type=Path,
                    help="the directory holding the scry-core, scry-mame and scry-dosbox-x "
                         "checkouts")
    ap.add_argument("--out", type=Path, default=Path("_site"),
                    help="where the site goes, replaced whole once it checks; default _site")
    args = ap.parse_args(argv)
    try:
        report = build(args.checkouts.expanduser(), args.out.expanduser())
    except Invalid as e:
        print(f"INVALID: {e}", file=sys.stderr)
        return 3
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
