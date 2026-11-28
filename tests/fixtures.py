"""Small git repositories in the shape the three SCRY repositories have, for the build's tests."""

from __future__ import annotations

import struct
import subprocess
from pathlib import Path

CREDITS = "Developed by Optimiza ([the author](https://example.org/a)), with [friends](https://example.org/b)."
CLIENTS = (("Claude Code", "sh", "claude mcp add --scope user {key} -- uv run --directory \"$PWD\" "
            "scry-{key}"),
           ("Cursor", "json", '{{\n  "mcpServers": {{\n    "{key}": {{"command": "uv"}}\n  }}\n}}'))


def webp(width: int, height: int, frames_ms: tuple[int, ...]) -> bytes:
    """An animated WebP's chunks as a reader of its size and timing sees them."""
    body = b"VP8X" + struct.pack("<I", 10) + bytes(4) + (width - 1).to_bytes(3, "little") \
        + (height - 1).to_bytes(3, "little")
    for ms in frames_ms:
        frame = bytes(12) + ms.to_bytes(3, "little") + bytes(1)
        body += b"ANMF" + struct.pack("<I", len(frame)) + frame
    return b"RIFF" + struct.pack("<I", 4 + len(body)) + b"WEBP" + body


def install_block(key: str) -> str:
    parts = []
    for i, (name, lang, code) in enumerate(CLIENTS):
        parts.append(f"<details{' open' if i == 0 else ''}><summary>{name}</summary>\n\n"
                     f"Run this for {name}, and `x list` shows it.\n\n```{lang}\n"
                     f"{code.format(key=key)}\n```\n\n</details>")
    return "\n\n".join(parts)


def server_readme(key: str, label: str, demo: str) -> str:
    return f"""<h1 align="center">
  <img src="docs/logo.png" alt="SCRY" width="240"><br>
  scry-{key}
</h1>

<p align="center"><b>Ask your client what a {label} program is doing.</b></p>

<!-- demo-lead:begin {demo} -->
<p align="center"><a href="demos/{demo}/"><picture><source media="(prefers-reduced-motion: reduce)" srcset="demos/{demo}/screen.png"><img src="demos/{demo}/loop.webp" alt="The {demo} demo moving"></picture></a></p>

<table align="center">
<tr><th align="left">You ask</th><td>Write the line.</td></tr>
<tr><th align="left">Your client calls</th><td><code>write(ref="x")</code></td></tr>
<tr><th align="left">SCRY answers</th><td><code>{{"verified": true}}</code></td></tr>
</table>
<!-- demo-lead:end {demo} -->

scry-{key} is an MCP server for {label}.

## Install

You need git, [uv](https://docs.astral.sh/uv/) and a {label} with its debugger.

```sh
git clone https://github.com/scry-mcp/scry-{key}
cd scry-{key}
```

### Add it to your client

<!-- scry-install:begin -->
{install_block(key)}
<!-- scry-install:end -->

### Your first question

It needs only the {demo} demo:

> Start `{demo}` and show me
> the screen.

Your client calls `start`.

## What you can ask

- **"Who writes this byte?"** `watch_add`. The game stops on the write.
- **"Where is the score?"** `scan`, `watch_add`. A scan narrows it.

## See it run

- [`demos/{demo}/`](demos/{demo}/): the {demo} demo, run
  by its own script.

## Platforms

macOS and Windows. Each, said in [Session](REFERENCE.md#the-session).

## Credits

{CREDITS}
"""


REFERENCE = """# scry-{key}: reference

## Index

<!-- scry-reference:begin index -->
- [Session](docs/reference/session.md): Starting and ending a session. [`start`](docs/reference/session.md#start)
- [Breakpoints](docs/reference/breakpoints.md): Breakpoints and watches. [`watch_add`](docs/reference/breakpoints.md#watch_add), [`scan`](docs/reference/breakpoints.md#scan)
- [Names](docs/reference/names.md): Names and what they mean. [`disassemble`](docs/reference/names.md#disassemble), [`knowledge_find`](docs/reference/names.md#knowledge_find)
<!-- scry-reference:end index -->

## The session

The [README](README.md) and the [licence](LICENSE).

## Knowledge base

A reply names a number from the base. See [the tools](docs/reference/names.md).
"""


WHOLE = '{"summary": "{name} score: armed"}'
#: A `knowledge_find` reply that answers with one entry, as the whole reply of its example.
BEHAVIOUR = ("The emulator ends the current program with the return code and hands control back "
             "to the parent, as the source comment says real MS-DOS does.")
FOUND = ('{\n  "summary": "kind call key 0x21/0x4C: exit",\n  "status": "ok",\n'
         '  "entries_total": 1,\n'
         '  "entries": [{"id": "a:call:1", "kind": "call", "key": "0x21/0x4C", "name": "exit",\n'
         '               "description": "Ends the program with return code AL.",\n'
         f'               "behaviour": "{BEHAVIOUR}"}}],\n'
         '  "served": 3,\n  "held_back": 2\n}')


def entry(name: str, *, related: str = "", modes: bool = False, second: bool = False,
          whole: str = "", reads: str = "") -> str:
    then = ("Then let it run:\n\nCall:\n\n```text\nresume(seconds=60)\n```\n\n"
            "Reply, 1 of 9 fields:\n\n```json\n{\"verdict\": \"OTHER_STOP\"}\n```\n\n"
            if second else "")
    table = ("### The two modes\n\n| mode | what it does |\n|---|---|\n| `show` | Reads. |\n"
             "| `change` | Stops. |\n\n" if modes else "")
    return f"""<!-- scry-reference:begin {name} -->
## `{name}`

Do what {name} does, by name.

```text
{name}(ref, mode="show")
```

### Try it

On the demo, stopped.

Ask:

> Use {name} on the score.

Call:

```text
{name}(ref="score")
```

Reply, 2 of 5 fields:

```json
{{
  "summary": "{name} score: armed",
  "status": "ok",
  "length": 2
}}
```

{then}{reads or "`armed` means it is set. See [the states](#what-each-state-means)."}

<details><summary>The reply, whole</summary>

```json
{whole or WHOLE.replace("{name}", name)}
```

</details>

{table}### Arguments

- `ref` (string, required): What to use.
- `mode` (one of `"show"`, `"change"`, default `"show"`): How.

### What comes back

- `state`: `armed` when set.

<details><summary>All 1 reply fields</summary>

- `state` (string)

</details>

### What it refuses

- A name that matches several symbols (`ambiguous_ref`).

### Why it works this way

Because the debugger compares one byte.

### Related tools

- [`start`](session.md#start){related}

### Built on

It stands on the debugger's own commands.
<!-- scry-reference:end {name} -->
"""


def family(title: str, *names: str) -> str:
    return (f"# The {title} tools\n\nThese tools {title.lower()}.\n\n"
            "## What each state means\n\n`armed` is set.\n\n") + "\n".join(
        entry(n, related="\n- [`watch_add`](#watch_add)" if "watch_add" in names else "",
              modes=n == "watch_add", second=n == "watch_add") for n in names)


def demo_readme(demo: str) -> str:
    return f"""# {demo.title()}: a demo of the game

<!-- demo-motion:begin -->
<p align="center"><picture><source media="(prefers-reduced-motion: reduce)" srcset="screen.png"><img src="loop.webp" alt="{demo} in play"></picture></p>

1. `input` drops a coin.
2. `state_write` loads the
   saved state.

<!-- moments-ms: 1000,3000 -->
<!-- demo-motion:end -->

The {demo} demo drops a coin and reads it back.

## Run it

```sh
uv run python demos/{demo}/demo.py
```

## Try it yourself

[Add the server](../../README.md#install) and ask it these.

<!-- demo-transcript:begin -->
### 1. Find the credits

Ask:

> Find the credits.

Call:

```text
scan(method="start")
```

Reply, 1 of 4 fields:

```json
{{"summary": "scan start: 64 KB"}}
```

The scan holds every byte.

<details><summary>The whole reply</summary>

```json
{{"summary": "scan start: 64 KB", "status": "ok"}}
```

</details>
<!-- demo-transcript:end -->

## Tools this demo uses

| Group | Tools |
|---|---|
| [Breakpoints](../../docs/reference/breakpoints.md) | `watch_add` |
"""


def names_family() -> str:
    return (family("Names", "disassemble", "knowledge_find")
            .replace(entry("knowledge_find"), entry("knowledge_find", whole=FOUND,
                                                        reads="One entry matches, so `entries` answers it whole. "
                                                              "`served` and `held_back` count what the base serves and holds back.")))


SCHEMES = '''from dataclasses import dataclass


@dataclass(frozen=True)
class Scheme:
    opens_at: str


SCHEMES = {"rbil61": Scheme("https://example.org/list"),
           "dosbox-x": Scheme("https://example.org/dosbox/{pin}/{path}"),
           "mame": Scheme("https://example.org/mame/{pin}/{path}"),
           "datasheet": Scheme("")}
'''


def core_files() -> dict[str, str | bytes]:
    """The part of scry-core a base is read through: its sources and the pins of the emulators."""
    return {
        "README.md": f"# scry-core\n\nShared.\n\n## Credits\n\n{CREDITS}\n",
        "docs/file-names.md": "# File names\n\nOne rule. See [the README](../README.md).\n",
        "src/scry_core/__init__.py": "",
        "src/scry_core/knowledge/__init__.py": "",
        "src/scry_core/knowledge/shared.py":
            'PINS = {"dosbox-x": "2a43c7335efd91f87bf5582245abdd5b3f18d5d4", '
            '"mame": "mame0289"}\n',
        "src/scry_core/knowledge/sources.py": SCHEMES}


def base_source(function: str, kinds: tuple[tuple[str, str], ...], held_back: int,
                faults: int) -> str:
    """A server's base: `kinds` are the `(kind, source scheme)` of each entry it serves."""
    return f'''from dataclasses import dataclass

from scry_core.knowledge.shared import PINS
from scry_core.knowledge.sources import SCHEMES


@dataclass(frozen=True)
class Entry:
    kind: str
    ref: str


class Base:
    held_back = {held_back}

    def entries(self):
        return [Entry(k, s + ":x") for k, s in {kinds!r}]

    def whole(self, e):
        scheme, locator = e.ref.split(":", 1)
        opens = SCHEMES[scheme].opens_at
        url = (opens.format(pin=PINS[scheme], path=locator)
               if "{{pin}}" in opens and scheme in PINS else opens)
        place = {{"where": locator}}
        if url:
            place["url"] = url
        return {{"sources": [place]}}

    def __len__(self):
        return len(self.entries())

    def faults(self):
        return ["a fault"] * {faults}


def {function}():
    return Base()
'''


def base_files(key: str, *, kinds: tuple[tuple[str, str], ...] = (
        ("call", "rbil61"), ("call", "dosbox-x"), ("error", "rbil61")), held_back: int = 2,
        faults: int = 0) -> dict[str, str | bytes]:
    """The package of server `key`, holding the function the site loads its base through."""
    if key == "dosbox-x":
        return {"src/scry_dosbox_x/__init__.py": "",
                "src/scry_dosbox_x/knowledge.py": base_source("base", kinds, held_back, faults)}
    return {"src/scry_mame/__init__.py": "", "src/scry_mame/knowledge/__init__.py": "",
            "src/scry_mame/knowledge/support.py": base_source("load", kinds, held_back, faults)}


def server(key: str, label: str, demo: str) -> dict[str, str | bytes]:
    return {
        **base_files(key),
        "docs/reference/names.md": names_family(),
        "README.md": server_readme(key, label, demo),
        "REFERENCE.md": REFERENCE.format(key=key),
        "LICENSE": "MIT\n",
        "CONTRIBUTING.md": "# Contributing\n\nRun the checks.\n",
        "docs/logo.png": b"\x89PNG",
        "docs/reference/session.md": family("Session", "start"),
        "docs/reference/breakpoints.md": family("Breakpoints", "watch_add", "scan"),
        f"demos/{demo}/README.md": demo_readme(demo),
        f"demos/{demo}/screen.png": b"\x89PNG",
        f"demos/{demo}/loop.webp": webp(640, 400, (500, 500, 1000, 2000)),
    }


def git_repo(root: Path, files: dict[str, str | bytes]) -> None:
    root.mkdir(parents=True)
    for rel, body in files.items():
        f = root / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, bytes):
            f.write_bytes(body)
        else:
            f.write_text(body, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)


def track(repo: Path, rel: str, body: str | bytes) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(body, bytes):
        f.write_bytes(body)
    else:
        f.write_text(body, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)


def make(base: Path) -> Path:
    git_repo(base / "scry-mame", server("mame", "MAME", "gridlee"))
    git_repo(base / "scry-dosbox-x", server("dosbox-x", "DOSBox-X", "monkey"))
    git_repo(base / "scry-core", core_files())
    return base
