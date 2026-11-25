"""What each server's knowledge base serves, counted by the base's own code, and the two places
the site shows it: a section of the home and the page "Knowledge base".

The counts are never typed: a build asks each checkout's base, in a process of its own, what it
serves."""

from __future__ import annotations

import dataclasses
import html
import json
import re
import subprocess
import sys
from dataclasses import dataclass

from scry_site.example import Example
from scry_site.sources import Invalid, Repo

OUT = "knowledge/index.html"
DESCRIPTION = ("What the two SCRY servers call the numbers in a reply, and what their knowledge "
               "bases serve.")
#: How long a value of an entry may run in a pane before it is cut with an ellipsis.
CUT = 110
TITLE = "Knowledge base"
#: The fields of a `knowledge_find` reply that count what the base holds, which no page shows.
BOOKKEEPING = ("served", "held_back")
#: The heading each server's reference gives its own section on the base, as an anchor.
SECTION = "knowledge-base"
#: Where each server's package loads its base: the module and the function that returns it.
LOADERS = {"dosbox-x": ("scry_dosbox_x.knowledge", "base"),
           "mame": ("scry_mame.knowledge.support", "load")}
#: A `kind` of `knowledge_find`, in plain words, as the page lists it beside the value.
#: A source an entry cites, by the scheme of its reference: what the page calls it.
SCHEMES = {"rbil61": "Ralf Brown's Interrupt List",
           "dosbox-x": "DOSBox-X's source, at the commit the entries cite",
           "mame": "MAME's source, at the release the entries cite",
           "datasheet": "The makers' datasheets and manuals"}
#: Where a reader opens an emulator's source as a whole, at the pin the base names.
TREES = {"dosbox-x": "https://github.com/joncampbell123/dosbox-x/tree/{pin}",
         "mame": "https://github.com/mamedev/mame/tree/{pin}"}

# Runs with the checkouts' `src` folders and the standard library alone on its path (`-S` leaves
# site-packages out, `-B` writes no bytecode into a checkout), so no server is installed to count
# what it serves.
_ASK = """
import importlib, json, sys
from collections import Counter
sys.path[:0] = sys.argv[1:3]
from scry_core.knowledge import shared
from scry_core.knowledge.sources import SCHEMES
base = getattr(importlib.import_module(sys.argv[3]), sys.argv[4])()
kinds = Counter(e.kind for e in base.entries())
cited = Counter(s.ref.split(":", 1)[0] for e in base.entries() for s in e.sources)
print(json.dumps({
    "served": len(base), "faults": len(base.faults()),
    "kinds": kinds.most_common(), "cited": cited.most_common(),
    "opens": {name: s.opens_at for name, s in SCHEMES.items()}, "pins": dict(shared.PINS)}))
"""


@dataclass(frozen=True)
class Served:
    """What one server's base serves: how many entries, how many of each kind, and the sources
    its entries cite, each with where a reader opens it."""

    repo: Repo
    served: int
    kinds: tuple[tuple[str, int], ...]
    sources: tuple[tuple[str, str], ...]


def read(core: Repo, server: Repo) -> Served:
    """Ask `server`'s base what it serves. A base that cannot be loaded, reports a fault or
    serves nothing is refused: a count of nothing is not shown as a count."""
    module, function = LOADERS[server.key]
    where = f"{server.name}: its knowledge base"
    try:
        done = subprocess.run(
            [sys.executable, "-I", "-S", "-B", "-c", _ASK, str(core.root / "src"),
             str(server.root / "src"), module, function],
            capture_output=True, text=True, timeout=120, check=False)
    except (OSError, ValueError, subprocess.TimeoutExpired) as e:
        raise Invalid(f"{where} could not be asked: {e}") from e
    if done.returncode != 0:
        last = done.stderr.strip().splitlines()[-1:] or ["no message"]
        raise Invalid(f"{where} did not load ({module}.{function}): {last[0]}")
    try:
        got = json.loads(done.stdout)
    except ValueError:
        raise Invalid(f"{where} did not answer with its counts: {done.stdout[:80]!r}") from None
    if got["faults"] or not got["served"]:
        raise Invalid(f"{where} serves {got['served']} entries with {got['faults']} faults")
    sources = []
    for scheme, _ in got["cited"]:
        opens = got["opens"].get(scheme, "")
        if scheme in TREES and scheme in got["pins"]:
            opens = TREES[scheme].format(pin=got["pins"][scheme])
        elif "{" in opens:
            opens = ""
        sources.append((scheme, opens))
    return Served(server, got["served"], tuple((k, n) for k, n in got["kinds"]), tuple(sources))


def home(all_served: list[Served], example_html: str) -> str:
    """The home's section: one real question to the base, and where its names come from."""
    first = all_served[0] if all_served else None
    label = f" for {html.escape(first.repo.label)}" if first is not None else ""
    return (f'<div class="known">{example_html}</div>'
            f'<p class="more">Where a name comes from, and what the base{label} holds: '
            f'<a href="{OUT}">{TITLE}</a>.</p>')


def line(all_served: list[Served], href: str) -> str:
    """One sentence for the reference index, leading to the page."""
    return (f'<p class="muted">A reply names the numbers it shows from '
            f'<a href="{href}">the knowledge base</a>, whose entries are checked against their '
            f'source.</p>')


def column(s: Served, others: list[Served], example_html: str,
           links: list[tuple[str, str]]) -> str:
    """One server's half of the page: what its base serves, by kind and by source, one question
    asked of it, and where to read on. A source that is another emulator's is explained."""
    kinds = "".join(f"<li><code>{html.escape(k)}</code></li>" for k, _n in s.kinds)
    cited = "".join(
        "<li>" + (f'<a href="{html.escape(opens)}">{html.escape(SCHEMES.get(scheme, scheme))}</a>'
                  if opens else html.escape(SCHEMES.get(scheme, scheme))) + "</li>"
        for scheme, opens in s.sources)
    more = "".join(f'<li><a href="{href}">{text}</a></li>' for text, href in links)
    key = s.repo.key
    foreign = [o.repo.label for o in others if o.repo.key in dict(s.sources)]
    shared = (f'<p class="muted">Some of its entries are the chips both emulators share, so they '
              f"cite {html.escape(' and '.join(foreign))}'s source.</p>" if foreign else "")
    return (
        f'<section><h2 id="{key}">{html.escape(s.repo.label)}</h2>'
        f'<h3 id="{key}-kinds">What it names</h3><ul class="toollist kinds">{kinds}</ul>'
        f'<h3 id="{key}-sources">Checked against</h3><ul class="cited">{cited}</ul>{shared}'
        f'<h3 id="{key}-ask">Ask it</h3>{example_html}'
        f'<h3 id="{key}-more">Read on</h3><ul class="related">{more}</ul></section>')


def page(crumbs: str, columns: list[str]) -> str:
    return (
        f"{crumbs}<h1>{TITLE}</h1>"
        "<p class=lead>A reply calls a number by its name, and <code>knowledge_find</code> says "
        "what that number does.</p>"
        "<p>A name comes from your program's symbols first, then from the server's own "
        "knowledge base. Each entry is checked against the source it cites, and a number the "
        "base has no entry for stays a number.</p>"
        f'<div class="refcols">{"".join(columns)}</div>')


def _cut(text: str) -> str:
    if len(text) <= CUT:
        return text
    return text[:CUT].rsplit(" ", 1)[0].rstrip(",;:") + "…"


def entry_example(ex: Example, where: str) -> Example:
    """`ex`, the example of `knowledge_find`, as the knowledge base is shown by it: its one call
    answered by the entry (its name, what it is and what it does) cut to a pane, and without the
    fields and the sentence that count what the base holds. The reply must be one named entry."""
    m = re.search(r"```json\n(.*?)\n```", ex.whole, re.S)
    try:
        reply = json.loads(m[1]) if m else None
    except json.JSONDecodeError:
        reply = None
    entries = reply.get("entries") if isinstance(reply, dict) else None
    if not (m and isinstance(reply, dict) and isinstance(entries, list) and len(entries) == 1
            and isinstance(entries[0], dict) and "name" in entries[0]):
        raise Invalid(f"{where}: the whole reply is not one that answers with a single named "
                      "entry, which is the example the knowledge base is shown by")
    whole = {k: v for k, v in reply.items() if k not in BOOKKEEPING}
    entry = {k: _cut(str(entries[0][k])) for k in ("name", "description", "behaviour")
             if k in entries[0]}
    shown = {"summary": reply.get("summary"), "entries": [entry]}
    sentences = re.split(r"(?<=[.!?])\s+", ex.reads)
    counted = re.compile(rf"\b({'|'.join(BOOKKEEPING)})\b")
    reads = " ".join(t for t in sentences if not counted.search(t))
    if not reads:
        raise Invalid(f"{where}: its only reading sentence is about what the base holds, and "
                      "the knowledge base is shown without it")
    call = dataclasses.replace(ex.calls[0], fields=f"{len(shown)} of {len(whole)} fields",
                               reply=json.dumps(shown, indent=2, ensure_ascii=False))
    folded = (ex.whole[:m.start(1)] + json.dumps(whole, indent=2, ensure_ascii=False)
              + ex.whole[m.end(1):])
    return dataclasses.replace(ex, calls=(call,), reads=reads, whole=folded)
