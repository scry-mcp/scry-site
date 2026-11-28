"""The reference: one page per tool, made from its entry in its family's page, and the family's
own page, which lists its tools."""

from __future__ import annotations

import html
import posixpath
import re
from collections.abc import Callable
from dataclasses import dataclass

from scry_site import example, render
from scry_site.sources import ENTRY, Family, Invalid, Page, paragraphs

#: The sections of a tool's entry, in their order; a table of modes may stand after the first.
SECTIONS = ("Try it", "Arguments", "What comes back", "What it refuses", "Why it works this way",
            "Related tools", "Built on")
_ARGUMENT = re.compile(r"- `(\w+)` \((.+?)\): (.+)", re.S)
_FIELD = re.compile(r"- `(\w+)`: (.+)", re.S)


@dataclass
class Tool:
    family: Family
    name: str
    markdown: str
    out: str
    what: str
    signature: str
    sections: list[tuple[str, str]]

    @property
    def page(self) -> Page:
        """The tool's page, as the link resolver and the shell see it: part of its family's
        source."""
        f = self.family.page
        return Page(f.repo, f.src, self.out, "reference", self.markdown, title=self.name,
                    label=self.name)


def tools(family: Family) -> list[Tool]:
    """Every entry of `family`, cut into the parts a tool's page shows."""
    found = []
    page = family.page
    where = f"{page.repo.name}/{page.src}"
    for m in ENTRY.finditer(page.markdown):
        name, body = m[1], m[2]
        head = re.match(rf"## `{name}`\n\n([^\n]+)\n\n```text\n((?s:.+?))\n```\n\n", body)
        if not head:
            raise Invalid(f"{where}: the entry of {name} does not open with '## `{name}`', one "
                          "sentence and its signature in a ```text block")
        parts = re.split(r"^### (.+)\n", body[head.end():], flags=re.M)
        if parts[0].strip():
            raise Invalid(f"{where}: the entry of {name} holds text before its first '### '")
        sections = list(zip(parts[1::2], parts[2::2], strict=True))
        titles = [t for t, _ in sections]
        known = [t for t in titles if t in SECTIONS]
        extra = [t for t in titles if t not in SECTIONS]
        if (titles[:1] != ["Try it"] or known != [t for t in SECTIONS if t in known]
                or any(not t.startswith("The ") for t in extra) or titles[-1] != SECTIONS[-1]):
            raise Invalid(f"{where}: the entry of {name} has the sections {titles}; a tool's page "
                          f"shows {', '.join(SECTIONS)} in that order, a 'The ...' table after "
                          "'Try it'")
        out = posixpath.join(posixpath.dirname(page.out), f"{name}.html")
        found.append(Tool(family, name, body, out, " ".join(head[1].split()), head[2],
                          sections))
    return found


def anchors(family: Family, ts: list[Tool]) -> dict[tuple[str, str, str], str]:
    """Each heading of a tool's entry, by the id it has on the family's page, to the tool's page
    and the id it has there."""
    page = family.page
    whole = render.heading_ids(page.markdown)
    moved: dict[tuple[str, str, str], str] = {}
    for t, m in zip(ts, ENTRY.finditer(page.markdown), strict=True):
        first = page.markdown.count("\n", 0, m.start(2))
        last = first + m[2].count("\n")
        here = [i for line, i in whole if first <= line <= last]
        own = [slug(title) for title, _ in t.sections]
        if len(here) != len(own) + 1:
            raise Invalid(f"{page.repo.name}/{page.src}: the entry of {t.name} holds headings "
                          "other than its own name and its sections")
        moved[(page.repo.key, page.src, here[0])] = t.out
        for i, s in zip(here[1:], own, strict=True):
            moved[(page.repo.key, page.src, i)] = f"{t.out}#{s}"
    return moved


def slug(title: str) -> str:
    return str(render.heading_ids(f"## {title}\n")[0][1])


def _definitions(md: str, pattern: re.Pattern[str], where: str,
                 inline: Callable[[str], str]) -> tuple[str, str]:
    """A list of `- \\`name\\` ...` items as a definition list, and what follows the list; a
    section that opens with a sentence ("Takes no argument.") has no list."""
    blocks = paragraphs(md.strip())
    if not blocks or not blocks[0].startswith("- "):
        return "", md
    items = re.split(r"\n(?=- )", blocks[0])
    rows = []
    for item in items:
        m = pattern.fullmatch(item)
        if not m:
            raise Invalid(f"{where}: {item[:60]!r} is not '- `name` ...' as the list expects")
        if pattern is _ARGUMENT:
            kind = html.escape(m[2])
            kind = re.sub(r"`([^`]+)`", r"<code>\1</code>", kind)
            kind = re.sub(r", required$", ', <span class="req">required</span>', kind)
            rows.append(f"<div><dt>{m[1]} <small>{kind}</small></dt>"
                        f"<dd>{inline(' '.join(m[3].split()))}</dd></div>")
        else:
            rows.append(f"<div><dt>{m[1]}</dt><dd>{inline(' '.join(m[2].split()))}</dd></div>")
    return f'<dl class="args">{"".join(rows)}</dl>', "\n\n".join(blocks[1:])


def main(t: Tool, *, server: str, server_key: str, crumbs: str,
         inline: Callable[[str], str], block: Callable[[str], str]) -> str:
    """The tool's page: the example first, the contract after."""
    where = f"{t.family.page.repo.name}/{t.family.page.src}, {t.name}"
    tag = "mame" if server_key == "mame" else "dos"
    parts = [
        crumbs,
        '<header class="cmd-head">',
        f'<p class="tags"><span class="tag {tag}">{html.escape(server)}</span>'
        f'<span class="tag">{html.escape(t.family.page.label)}</span></p>',
        f'<h1 class="cmd-name">{t.name}</h1>',
        f'<p class="cmd-what">{inline(t.what)}</p>',
        f'<p class="sig">{html.escape(t.signature)}</p>',
        "</header>"]
    for title, md in t.sections:
        parts.append(f'<h2 id="{slug(title)}">{html.escape(title)}</h2>')
        if title == "Try it":
            ex = example.parse(md, where, located=True)
            parts.append(example.render(ex, caption=inline(ex.where), inline=inline, block=block))
        elif title == "Arguments":
            dl, rest = _definitions(md, _ARGUMENT, where, inline)
            parts.append(dl + (block(rest) if rest else ""))
        elif title == "What comes back":
            dl, rest = _definitions(md, _FIELD, where, inline)
            parts.append(dl + (block(rest) if rest else ""))
        elif title == "Related tools":
            parts.append(block(md).replace("<ul>", '<ul class="related">', 1))
        else:
            parts.append(block(md))
    return "\n".join(parts)


def family_main(f: Family, ts: list[Tool], body: str, crumbs: str,
                inline: Callable[[str], str]) -> str:
    """The family's page: its own text, then its tools, each a link and its sentence."""
    rows = "".join(f'<li><a href="{posixpath.basename(t.out)}"><code>{t.name}</code></a>'
                   f"<span>{inline(t.what)}</span></li>" for t in ts)
    return (f'{crumbs}{body}<h2 id="the-tools">The tools</h2>'
            f'<ul class="toollist">{rows}</ul>')


def without_entries(md: str) -> str:
    """A family's page with its tools' entries taken out: what its own page shows."""
    return ENTRY.sub("", md)
