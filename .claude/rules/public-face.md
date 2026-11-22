---
paths:
  - "README.md"
  - "scry_site/templates/**"
  - "scry_site/static/**"
  - "scry_site/build.py"
  - "scry_site/render.py"
  - "scry_site/analytics.py"
  - "scry_site/seo.py"
---

> **This is the public-face profile of this repository.** It loads when one of the files below is
> opened, and it says who each page of the site is written for, how much it may say, and how it
> looks. It is reference, not a task list.

## The layers of the public face

| layer | where it is made | audience | character |
|---|---|---|---|
| home | `scry_site/templates/landing.html`, the home's own words in `scry_site/build.py` | a stranger deciding in a minute whether SCRY is worth installing | one screen says what SCRY does for them, with a demo moving and one real question answered; then the install per client; then what one can ask, the demos, the two servers |
| command page | generated, one page per tool, from the servers' reference | somebody using a server who wants one tool: what to ask, what to send, what comes back | the example first, the contract after; read on a phone |
| family page and reference index | generated from each server's `REFERENCE.md` and `docs/reference/*.md` | somebody looking for the tool that does a thing | a list: each tool's name and its one sentence, linked |
| demo page | generated from each `demos/*/README.md` | somebody who wants to watch one investigation and try a step of it | the moving picture and its moments, what it shows, the one command, steps to try, the tools it uses, more demos |
| document page | generated from every other public markdown (front doors, contributing, scry-core's docs) | that document's own reader | the document as written, in the site's type |
| privacy and cookies pages | `scry_site/analytics.py` | a visitor deciding whether to accept measurement | who runs the site, what is collected and the cookies it sets, how to change the choice; each at most one screen, in plain words |
| consent banner | `scry_site/analytics.py`, `scry_site/static/consent.js` | a first-time visitor on any page | one short notice above the bar with two buttons of equal weight, Reject and Accept; shown only on a build that has a property id and only until a choice stands |
| repository front door | `README.md` | somebody changing the site | practical and short: the commands, what each proves |

Language: English, every layer. This line is the declaration.

## What is public and what is not

- Public: the built site and this repository's `README.md`.
- Every word the site shows about a server is read out of that server's repository at build
  time. Written here are only the home's hero, the section headings, the navigation labels and
  the page titles. A finding about a generated page is a finding about the repository it came
  from, fixed there.

## Countable limits

| layer | limit |
|---|---|
| home | at most 80 words between the top of the page and the install block, the exchange under the demo included |
| home | hero: the logo, one heading of at most 5 words, one paragraph of at most 40 words, two buttons |
| home | hero: one demo's moving picture, its moments named under it (at most 3, each at most 6 words), and one exchange of three rows: what was asked, the call, the reply |
| home | every section opens with its number, its title and one lead of at most 25 words |
| home | install: three numbered steps; one emulator switch and one client strip; one block showing per step |
| home | "What you can ask": at most 6 cards, each a question of at most 12 words, the tools, and one sentence of at most 20 words |
| home | demos: at most 8, each a moving picture, a name and one sentence of at most 20 words |
| every page | a paragraph is at most 3 sentences and 60 words; a sentence at most 30 words |
| every page | a table has at most 3 columns and 12 rows; wider data is a definition list |
| every page | a visible code block has at most 12 lines; longer output sits in a closed `<details>` |
| every page | no horizontal scroll at 390 px: `document.documentElement.scrollWidth` equals the viewport |
| every page | no text under 13 px; running text 16 px or more |

## The home's hero

- The picture is the Monkey Island demo's `loop.webp`: the lookout answers as the game wrote
  him, then with the line the demo wrote into memory.
- Under it, the picture's moments, numbered, each in at most 6 words; the one on screen is lit
  while it plays (*Demo motion*).
- Then one exchange in three rows. `You`: one request of at most 12 words. `Client`: the call
  as written, a long value cut with `…`. `SCRY`: the reply's own `summary`, or a figure read out
  of the reply.
- "The machine" is the emulated one, in the heading and everywhere else. The reply is SCRY's,
  and MAME and DOSBox-X are "the two emulators", never "machines".
- The exchange is copied from the demo's transcript, never typed.

## A command page: its fields and their order

1. The emulator and the family, as two tags. Beside the page (closed above it on a phone) the
   family's tools, headed by one sentence saying in plain words what the family holds. The
   crumbs above end, where the other server has the same tool, on `Also in <server>`.
2. The tool's name, in mono.
3. What it does for a person: one sentence, at most 25 words.
4. The signature, in muted mono, on its own line.
5. **Try it**: where it can be tried (a demo the reader can get, and the state it is in), then the
   example in the one shape below.
6. A table of modes or methods, where the tool has a `mode` or a `method`.
7. **Arguments**: a definition list in the signature's order: name, type, `required` or the
   default, one sentence.
8. **What comes back**: the fields a reader acts on, at most 6, each with one sentence; every
   field's name behind a closed `<details>`.
9. **What it refuses**: a list, one refusal a line, its code in mono.
10. **Why it works this way**: at most 3 paragraphs showing; more behind a closed `<details>`.
11. **Related tools**: the family's other tools and the ones its example calls, as links.

The page never shows a heading in code type on a tinted box, and never a value in the accent
colour with a glow.

## An example: its shape

One shape on every page that shows a call: the home, a command page, a demo page.

1. **Ask**: what a person would type to their client, at most 25 words, one request, with a
   copy button: it is what a reader pastes into their client.
2. **Call**: the call as written, `tool(argument=value)`, at most 3 lines, in a pane headed `CALL`.
   A call and its reply are one block, the reply hanging under its call; a second call is
   introduced by one line saying what happened in between.
3. **Reply**: an excerpt of the real reply in a pane headed `REPLY`, at most 12 lines, with
   "N of M fields" in the pane's header.
4. How to read that reply: at most 2 sentences and 40 words, which say in plain words any name
   of ours the excerpt shows (*Vocabulary*).
5. The whole reply behind a closed `<details>`.

A reply is copied from a run (the server's `docs/reference/examples.json`, a demo's transcript),
never typed. An example has at most two calls.

## Demo motion

- A demo is shown moving wherever it appears: its animated WebP (`loop.webp`), never a still
  alone. The still (`screen.png`) is what a reader who asks for reduced motion gets, through
  `<picture><source media="(prefers-reduced-motion: reduce)" srcset="screen.png">`.
- The file is the demo's own, made and limited by its server's profile. The site copies it and
  never re-encodes it.
- It is drawn inside the CRT frame, filling a 4:3 tube, with `image-rendering: pixelated`,
  `width` and `height` set, and `loading="lazy"` below the first screen.
- Where a program leaves the foot of its screen black, the page may cut the tube to the picture.
  The file stays whole.
- Under the hero's picture and a demo page's, the picture's moments are listed, numbered, and
  the page lights each one while it plays. The builder reads the frames' durations out of the
  file and writes one pair of keyframes a moment; the page's script starts the picture again
  from its first frame and the keyframes with it, on load and whenever the tab comes back.
  Without the script, or under reduced motion, every moment reads plain and none is lit.
- The home loads at most 1.5 MB of demo motion in all.

## The design system

The site is SCRY's own poster: a black ground, its red logo lit like a neon sign, and the texture
of a rented tape played on a tube. It has one colour scheme, dark, and no light one. The mood is
the horror and adventure films of the 1980s and the title cards that revive them, made with type,
colour, light and texture only. **No film's or series' logo, title lettering, typeface, name or
picture is used. No logo, icon, interface screenshot or font of MAME or DOSBox-X is used either,
and each of those two names appears as text.**

### Colour

Tokens, as `site.css` declares them in `:root`.

| token | value | use |
|---|---|---|
| `--bg` | `#000000` | the page, the top bar, a control at rest |
| `--surface` | `#0e0e10` | cards, example frames |
| `--surface2` | `#1a1a1e` | inline code, the current item, a key-bar label |
| `--line` | `#2a2a30` | rules and frames, decoration only |
| `--edge` | `#77777f` | the border of a control |
| `--fg` | `#ece8e1` | text: a warm white, never `#ffffff` for running text |
| `--muted` | `#a9a59d` | secondary text |
| `--link` | `#ffb0a8` | links, underlined in `--red` |
| `--red` | `#ff4a40` | titles in the display face, `required`, a refusal, numerals |
| `--blood` | `#c1121f` | light and rules: the bar's line, a pane's lamp, a card's top rule. Never text |
| `--btn` / `--onbtn` | `#c8161d` / `#ffffff` | the primary button, the chosen tab, the `Ask` tag |
| `--focus` | `#55ffff` | the focus ring, 2 px |
| `--screen`, `--screenbar` | `#08080a`, `#17171a` | a pane's background, its title strip |
| `--screenlabel`, `--screenfg`, `--screendim` | `#c9c5bd`, `#ece8e1`, `#9a968e` | a pane's label, its text, its quiet text |
| `--screenkey`, `--screennum`, `--screencall` | `#55ffff`, `#ffff55`, `#ff5555` | a JSON key, a number, a tool's name in a call |
| `--screenok`, `--screenbad` | `#55ff55`, `#ff5555` | `ok` and the shell prompt, `INVALID` |
| `--mamebox`, `--onmame`, `--onmame2` | `#12182a`, `#ffffff`, `#ffff55` | the MAME box |
| `--dos`, `--ondos`, `--ondos2` | `#000000`, `#aaaaaa`, `#ffffff` | the DOS screen |
| `--glow`, `--fog` | `255,45,40`, `193,18,31` | the colour of every glow and of the hero's fog, as `rgba()` parts |

A pane's five syntax colours are the bright half of the CGA and VGA text palette.

Every text-on-background pair, with its WCAG contrast ratio. Text needs 4.5 or more, a control's
border and the focus ring 3 or more. `fogpeak` is the lightest ground the hero's text can meet:
the fog at its centre with a scan line and a grain of the film over it. `grainpeak` is black
under a grain at full strength. The table is computed from `site.css`, and a pair added to the
site is added here with its ratio.

| text | on | ratio | floor |
|---|---|---|---|
| `fg` #ece8e1 | `bg` #000000 | 17.20 | 4.5 |
| `fg` #ece8e1 | `grainpeak` #0c0c0c | 16.02 | 4.5 |
| `fg` #ece8e1 | `surface` #0e0e10 | 15.79 | 4.5 |
| `fg` #ece8e1 | `surface2` #1a1a1e | 14.21 | 4.5 |
| `fg` #ece8e1 | `fogpeak` #42181b | 12.48 | 4.5 |
| `muted` #a9a59d | `bg` #000000 | 8.56 | 4.5 |
| `muted` #a9a59d | `grainpeak` #0c0c0c | 7.97 | 4.5 |
| `muted` #a9a59d | `surface` #0e0e10 | 7.86 | 4.5 |
| `muted` #a9a59d | `surface2` #1a1a1e | 7.07 | 4.5 |
| `muted` #a9a59d | `fogpeak` #42181b | 6.21 | 4.5 |
| `link` #ffb0a8 | `bg` #000000 | 12.03 | 4.5 |
| `link` #ffb0a8 | `grainpeak` #0c0c0c | 11.20 | 4.5 |
| `link` #ffb0a8 | `surface` #0e0e10 | 11.04 | 4.5 |
| `link` #ffb0a8 | `surface2` #1a1a1e | 9.94 | 4.5 |
| `red` #ff4a40 | `bg` #000000 | 6.31 | 4.5 |
| `red` #ff4a40 | `grainpeak` #0c0c0c | 5.87 | 4.5 |
| `red` #ff4a40 | `surface` #0e0e10 | 5.79 | 4.5 |
| `red` #ff4a40 | `surface2` #1a1a1e | 5.21 | 4.5 |
| `red` #ff4a40 | `fogpeak` #42181b | 4.58 | 4.5 |
| `onbtn` #ffffff | `btn` #c8161d | 5.85 | 4.5 |
| `bg` #000000 | `fg` #ece8e1 | 17.20 | 4.5 |
| `screenlabel` #c9c5bd | `screenbar` #17171a | 10.40 | 4.5 |
| `screenlabel` #c9c5bd | `bg` #000000 | 12.20 | 4.5 |
| `screenfg` #ece8e1 | `screen` #08080a | 16.39 | 4.5 |
| `screendim` #9a968e | `screen` #08080a | 6.79 | 4.5 |
| `screenkey` #55ffff | `screen` #08080a | 16.33 | 4.5 |
| `screennum` #ffff55 | `screen` #08080a | 18.76 | 4.5 |
| `screencall` #ff5555 | `screen` #08080a | 6.37 | 4.5 |
| `screenok` #55ff55 | `screen` #08080a | 15.08 | 4.5 |
| `screenbad` #ff5555 | `screen` #08080a | 6.37 | 4.5 |
| `screenok` #55ff55 | `bg` #000000 | 15.82 | 4.5 |
| `onmame` #ffffff | `mamebox` #12182a | 17.65 | 4.5 |
| `onmame2` #ffff55 | `mamebox` #12182a | 16.55 | 4.5 |
| `ondos` #aaaaaa | `dos` #000000 | 9.04 | 4.5 |
| `ondos2` #ffffff | `dos` #000000 | 21.00 | 4.5 |
| `dos` #000000 | `ondos` #aaaaaa | 9.04 | 4.5 |
| `edge` #77777f | `bg` #000000 | 4.73 | 3.0 |
| `edge` #77777f | `surface` #0e0e10 | 4.34 | 3.0 |
| `edge` #77777f | `fogpeak` #42181b | 3.43 | 3.0 |
| `focus` #55ffff | `bg` #000000 | 17.13 | 3.0 |
| `focus` #55ffff | `surface` #0e0e10 | 15.73 | 3.0 |
| `focus` #55ffff | `surface2` #1a1a1e | 14.16 | 3.0 |
| `focus` #55ffff | `fogpeak` #42181b | 12.43 | 3.0 |
| `focus` #55ffff | `mamebox` #12182a | 14.40 | 3.0 |

Never: text in `--blood` or `--line`; red for running text; a white brighter than `--fg` for a
paragraph; a second accent colour on the page outside a pane and the two emulators' boxes.

### Type

Four faces, served with the site under the SIL Open Font License (`scry_site/static/fonts/`, each
licence file beside its font). No font, style or picture is requested from another host. The one
script that is is Google Analytics' tag, from `googletagmanager.com`, which `consent.js` loads
only after the visitor accepts, only on the production host, and never on a build with no
property id.

Fraunces is the display face. It is an old-style soft serif drawn after Windsor, Souvenir and the
Cooper faces, the family of the paperback covers and title cards of the period. Set in capitals
and spaced wide, it carries the mood without copying any title's lettering. It is set with `SOFT`
0 and `WONK` 0, as one variable file cut to the Latin range.

| role | face | phone (390 px) | desktop (1440 px) |
|---|---|---|---|
| the home's heading | Fraunces 800, capitals, spaced 0.05 em | 36 px | 64 px |
| the home's section titles | Fraunces 700, capitals, spaced 0.1 em | 25 px | 32 px |
| numerals, the two emulators' titles, the tape's lines | VT323 | 22 to 32 px | 22 to 32 px |
| a picture's moments | IBM Plex Sans 400 beside a VT323 numeral | 15 to 16 px | 16 to 17 px |
| page title (`h1`) | IBM Plex Sans 700 | 28 px | 40 px |
| a tool's name | IBM Plex Mono 600 | 28 px | 40 px |
| section (`h2`) | IBM Plex Sans 700 | 22 px | 26 px |
| subsection (`h3`) | IBM Plex Sans 700 | 18 px | 20 px |
| lead, the sentence under a title | IBM Plex Sans 400 | 19 px | 19 px |
| running text | IBM Plex Sans 400 | 16 px | 17 px |
| secondary text, captions | IBM Plex Sans 400 | 14 to 15 px | 15 px |
| code in a pane | IBM Plex Mono 400 | 14 px | 14.4 px |
| labels in capitals (tags, pane headers, the bar) | IBM Plex Mono 600 | 13 px | 13 to 14 px |

- Line height 1.6 for running text, 1.55 in a pane, 1.2 for headings, 1.04 for the display face.
  A line of prose is at most 68 characters wide.
- Fraunces is for the home's heading and its section titles only: never a sentence, a tool's
  name, a page title of a document or a control.
- VT323 is never under 22 px and never a sentence.
- Inline code is 0.9 em and never under 13 px, on `--surface2`, with no border.

### Light and texture

Each effect is light behind or around the content. None lies over running text, code, a tool's
name or a value.

| effect | where | made of | limit |
|---|---|---|---|
| glow | the logo in the hero, the home's heading and section titles, the primary button, the bar's line, a pane's lamp | `text-shadow`, `box-shadow` or `drop-shadow` in `--glow` | never on a paragraph, a list, a table, a pane's text or a command page's title |
| fog | behind the hero | one radial gradient of `--fog`, fading out downwards | alpha 0.26 at most, so `--red` on `fogpeak` stays at 4.5 |
| scan lines | behind the hero; over a demo's picture | a 1 px line every 4 px at 3% white; every 3 px at 20% black on a picture | never over text |
| grain | the whole page, under everything | one still tile of noise, fixed, at 7% | under the content, never animated |
| colour fringe | the home's heading | a 1 px cyan and a 1 px red shadow | that heading only |
| tape band | the hero's picture and a demo page's | a pale band crossing the tube in 8 s | one per page |
| flicker | the logo in the hero | two dips, to 86% and to 90% of its light, in 9 s | under WCAG 2.3.1: fewer than three flashes a second, a small area, a small change |
| vignette | a demo's picture | a radial gradient darkening the tube's corners | on the picture only |
| moments lit | under the hero's picture and a demo page's | the sentence on screen in `--fg` and its numeral in `--red` with a glow, the others in `--muted`, changing in one step | colour only: no word appears, moves or goes |
| a tube warming up | a demo's picture under the pointer or the focus | the picture brightens once in 0.32 s, its scan lines roll, its glow rises | on the picture only |
| phosphor line | the top bar's link under the pointer, and the current one | a 2 px line of `--red` with a glow under it | the bar only |

Moving on a page: the flicker, the tape band, the DOS cursor, the demos' pictures, the light of
their moments and a tube under the pointer. Nothing else.

### Space and layout

- Spacing steps: 4, 8, 12, 16, 24, 32, 48, 64, 96 px. Nothing else.
- Breakpoints: 640 px (two columns of cards), 760 px (the top bar on one row), 960 px (the hero
  and the documentation's side list beside the text), 1100 px (three and four columns of cards).
- A command page has no right-hand column: its sections ("on this page") are listed in the left
  side list, nested under the command that is open there, so the command's own text takes the
  width. On a phone the side list, sections included, folds above the text.
- From 960 px the side list stays in view beside the text, with its own scroll when taller than
  the window, fits the room between the bar and the foot to the page's end, and keeps 24 px
  from the foot. On a command page it also marks the section being read and scrolls its own
  box, never the page, so the open command, that section and the next command stay in view.
- A command or family page's side list opens on one row, `◀ <server> reference`, the way up to
  the server's reference: on a phone the folded list's first row, from 960 px above the list's
  own scroll so it stays in view at any depth. The list ends on a `Families` group, every
  family of the server with the open one marked, reached by the list's own scroll.
- Under 960 px each link of the crumbs is 44 px high.
- Under 960 px a command page carries one link back to its tool list, fixed in the bottom-right
  corner, 44 px high, labelled `▲ Tools`. It lands on the list opened; with scripts off, on its
  closed summary. The foot leaves it room under its last line, and no focused control sits
  under it.
- The page is 1200 px wide at most, with 16 px at its sides on a phone and 24 px above 640 px.
- The top bar reaches every section at every width: Install, Demos, Reference, GitHub. Under
  760 px it is two rows, the logo and then the four links at equal widths, 44 px high; the links'
  row stays at the top as the page scrolls. No link is hidden at any width.
- On a phone the hero's first screen holds the bar, the logo, the heading, the sentence, the two
  buttons and the top of the moving picture.
- A link or control a finger takes is at least 44 px high; a pane's copy button at least 32 px.
- On a phone the family's tool list is closed above the page (`<details>`) and opens only when
  the reader taps it or its corner link; on a desktop it stands open beside it. A page never
  opens on its navigation.
- A pane wraps its lines at every width; a shell line that wraps hangs under its command, not
  under its prompt, and never breaks between the two hyphens of a `--flag`. Nothing a reader needs
  is reached by scrolling sideways.
- The home's sections are 64 px apart on a phone and 96 px from 960 px.
- A control sits beside what it changes: the emulator switch above the three steps, the client
  strip inside the step it changes. Both are grids of equal cells 44 px high; the clients are two
  columns on a phone and five from 640 px.
- On a phone a step's numeral sits beside its heading and the step takes the full width; from
  640 px the steps hang from one line, their numerals in its margin.
- The demos are a row each on a phone (the picture at 42%, the name and the sentence beside
  it), two cards a row from 640 px and four from 1100 px.
- On a phone a demo page reads: what it is, the picture, its moments right under it. From
  960 px the moments stand beside the picture.
- The foot holds, in this order: the key bar, the small logo with one line naming the three
  repositories and the links to the privacy and cookies pages, the credits line, and the tape's
  end. The links share the logo's row, so the foot is no taller for them.
  Under 960 px each of the two links is 44 px high, like any link a finger takes.
- The consent banner is in the page's flow above the top bar, never fixed over the text, so it
  covers no control and no side list. Its two buttons are 48 px high.

### Motifs: the homage

| motif | from | where | made of |
|---|---|---|---|
| the neon sign | a title card of the 1980s | the logo, the home's heading and section titles | SCRY's own logo and Fraunces in capitals, in red with a glow, a thin red rule fading to the right under a section title |
| the tape | a rented VHS | under the hero's picture and a demo page's; the foot of every page | one line in VT323: `▶ PLAY` in red, the demo's name and its length; the tape band over the tube. `▶` before "See it run". At the foot of every page `■ STOP` and `◀◀ REWIND`, which is the link back to the top |
| the CRT | an arcade monitor, a PC's monitor | every demo's picture | a dark bezel with round corners, scan lines and a vignette; the picture fills a 4:3 tube, as it did on the monitor it was made for |
| the pane | a debugger's window | every call, reply and shell line | a dark title strip with a red lamp and a capital label, a near-black screen, the sixteen-colour text palette for its syntax |
| the key bar | a DOS file manager's function-key line | the foot of every page | `F1` to `F5` in red on black, a label beside each, each a real link; on a phone the keys grow to fill their two rows |
| the MAME box | MAME's in-emulator menu | the MAME server's card | a slate box with a white rule and round corners, a centred pixel title, a marker beside the item under the pointer |
| the DOS screen | the DOS prompt | the DOSBox-X server's card | black, light grey text, a double grey rule, `C:\>` before the name, a `C:\SCRY>` line with a blinking cursor, the item under the pointer in inverse video |
| the numerals | a terminal | section numbers, the install's steps, a picture's moments, a demo's steps to try | VT323: `01` to `04` in `--muted` for a section, red in a red frame for an install step, red for a moment and a step to try |

A motif is decoration around the content, never over it. The logo is SCRY's own
(`scry-logo.png`): small in the bar, large and lit in the home's hero.

### One scheme, motion, scripts

- The site declares `color-scheme: dark` and has no rule under `prefers-color-scheme`.
- `prefers-reduced-motion: reduce` stops the flicker and the cursor, removes the tape band,
  shows each demo's still, leaves every moment unlit and keeps a tube's glow under the pointer
  without its bloom or its rolling lines. The glow stays: a sign that is lit, not one that is off.
- The site reads and works whole with scripts off: the install's switches are radio inputs read
  by CSS (`:has(:checked)`). One inline script of at most 2.5 KiB (2,560 bytes) adds the copy
  buttons (on every shell block and every ask), starts a picture's moments with the picture,
  fits the wide side list on every page that has one, and on a command page follows the section
  being read and opens the folded list from its corner link. It does nothing more.
- The consent script is a file of its own (`consent.js`), outside that inline budget. It asks
  before it measures: the four Consent Mode signals start denied, `analytics_storage` is granted
  only on Accept, a rejected or never-asked visitor is sent nothing, and the choice lasts six
  months. Without scripts the banner never appears and nothing is measured.
- Focus is always visible: a 2 px ring in `--focus`.

## Install on the home

- Three numbered steps: get the server, add it to your client, ask your first question.
- One switch for the emulator (MAME first) above the steps, and inside the second step one strip
  for the client, in this order: Claude Code,
  Codex, Claude Desktop, Cursor, VS Code, Copilot CLI, Gemini CLI, Antigravity, Devin, Another
  client. Claude Code is the one showing on arrival.
- Each client's block is the one its server's front door carries, read out of that README: the
  site never words an install of its own.
- The first question is the front door's, and needs nothing but a free mamedev.org ROM or a
  program the repository carries.

## A thing is called what it is, and a page never shows our bookkeeping

- **A title, a heading and a link's text name the thing itself**, in the words somebody who
  has never seen SCRY would use for it: "Knowledge base", never a phrase coined for its effect
  ("Names for numbers"). If the reader has to work out what the title refers to, the title is
  wrong.
- **A public page says what a reader gets, never how we are building it.** No count of what
  is written and not yet served, no state of our own pipeline ("held back", "pending",
  "confirmed by a second reader", "not complete yet"), no account of how an entry comes to be
  shown. What the thing has and what it answers is the whole of it; a product's page does not
  list its own backlog.
- **Where a reply shown as an example carries such fields, the page shows the reply without
  them.** They stay documented only where a tool's reply is described field by field, each in
  the words that field needs and no more.
- A sentence that describes our process and not what the visitor gets is a finding, and so is
  an option offered for a page that would expose it.

## Vocabulary: words a programmer who never saw SCRY knows

- Headings and running text use words a programmer who has never seen SCRY knows. A heading says
  what is under it in those words: "Tools this demo uses", never "What it walks".
- A term of ours appears only if it is the name of a tool, an argument, a reply field, one of
  its values, or a family of tools. It is set in code type (a family's name as a plain capital
  word), and where it first appears on a page it is explained in plain words, in that sentence
  or the next. A page is one document, or one page of the site.
- A wording a server prints inside a reply is shown as printed, because a reply is copied and
  never typed; the sentence that reads the reply says it in plain words.
- A metaphor is not a term. A thing is called what it is each time, even when a shorter image
  has become a habit here.
- An emulator's own vocabulary (MAME's, DOSBox-X's, DOS's) is used as its documentation uses it,
  and a word of it a programmer may not know is explained once the same way.
- The table is part of the rule. A word of its left column, used in that private sense in a
  heading or in running text, is a finding, and the right column is what to write. A coinage
  the table does not hold yet is a finding too: it is added with its plain words.
- This file's own labels for the layers ("front door", "demo guide") are names inside this
  file. A public document says "the README" and "the demo's page".

| ours | write |
|---|---|
| Names for numbers | Knowledge base |
| What it walks | Tools this demo uses |
| A first answer | Your first question |
| From an investigation to a bench | From a session to a test that replays itself |
| The battery | The checks |
| The live tier | Tests against a real emulator |
| The store | The `.scry/` folder / What is saved between sessions |
| The route | How input gets into the program |
| The code pane is the control | Checked against the debugger's own disassembly |
| The one table | Tools that answer while the program runs |
| Recipes | Start profiles |
| Sessions (in `.scry/`) | Saved step lists |
| Two machines | Two emulators |
| Shared core | scry-core, the shared package |
| walk | sequence of steps / destination rectangle / list of files |
| front door | the README |
| flow | the README's example calls |
| bench | replay test / folder of test programs / live-test helper |
| tier | tests against a real emulator / opt-in tests |
| battery | the checks |
| desk | your screen and keyboard |
| kata | checked demo |
| roster | tool list |
| envelope | the fields every reply carries |
| survey | the readings taken at each stop |
| store | the `.scry/` folder / the saved breakpoints file |
| recipe | start profile |
| park | stopped at the debugger |
| place | address / resolved to an address |
| census | write log |
| LATCHES | stays set until `close` |
| law | rule |
| rung, ladder | the first of these that is set |
| broom | way of clearing |
| golden, blessed | reference capture / reference build |
| held to | matches / is compared with |
| judged | checked |
| signed | fingerprinted |
| rest | confirmed stopped |
| fly | fast-forward |
| release | resume |
| alarms | warnings |
| ride | is included in |
| matrix, cell | the live test script / test case |
| probe | description test / version check |
| residual | known failure, tolerated |
| sweep | cleanup pass / manual check |
| gate | check |
| drift | out of date |
| surface | the tools and their replies |
| instrument | check |
| seam | test override |
| guardian | watchdog |
| highlight, epilogue | featured step / closing steps |
| the loop | the demo's clip |
| one-off images | say the thing itself |
| the owner, the reader | you |
| answer by name | by your program's symbol names |
| proves they landed | checks the program took them |
| the beam | the screen line being drawn |
| heavy debugger | a DOSBox-X built with heavy debugging |
| arrival | reaching the target |
| channel | log / debugger connection |
| stub | the input helper inside DOS |
| guest | the program (inside the emulator) |
| double | stand-in for tests |
| dumper | table writer |
| cold, hot | rarely run / often run |
| harness, binding | boot script / per-emulator settings |
| known answer | reference data |
| lap | repetition |
| batch | the loaded symbol table |
| scratch | temporary folder |
| cap | the client's text limit |
| ledger, canary | run log / preflight check |
| call boundary | call wrapper |
| fold | merged tool |
| bound | time limit |
| live run | a run against the real emulator |
| declare (a repository) | keeps in `.scry/` |

Kept and explained where they first appear, never renamed by a document:

- The families, by the names the servers send: Run (the tools that let the program run and stop it again), Breakpoints (breakpoints and watches, saved by name and set again by the server), Sequences (the tools that run several calls as one: `perform`, `drive`), Project (the tool that saves into the repository's `.scry/` folder: `promote`), Timeline (MAME's tools that show the frames in which a write happened). "Screen map" names the `screen_map_*` tools and the file they read: a program's screens and the named areas of each, explained where it first appears.
- The names: `promote`, `kept`, `draft`, `not_settled`, `settle_seconds`, `verdict`, `OTHER_STOP`, `ELAPSED`, `TARGET`, `TIMEOUT`, `altered`, `control`, `control_silent`, `anchor`, `mark`, `since_mark`, `ref`, `held`, `recorded`, `diverged`, `route`, `armed`, `pending`, `unresolved`, `unarmable`, `stale`, `foreign`, `inherited`, `orphan`, `declaration`, `regpoint`, `shared`, `presence`, `tally`, `show`, `change`, `count`, `capture`, `freeze`, `consolidated`, `verified`, `perform`, `drive`, `e9`, `no_channel`, `enrichment`, `unaccounted`, `surveyed`, `superseded`, `cut`, `posted`, `arrived`, `pen`, `profile`, `keep_noise`, `heavy_debug`, and every other tool, argument, field and value the reference lists.
- What a reply prints: "survivors"; "posted, unverified / effect seen"; "retraces"; "kept N (promote to review)"; "<volatile>, <host>, <run>, <time>".

## Limits

- The README closes with the credits line, verbatim, its links resolving; every page's footer
  renders that line, read out of scry-core's README with the author's link read as
  `https://github.com/Optimiza` (the READMEs keep LinkedIn; the build refuses any other mention
  of LinkedIn):

  `Developed by Optimiza ([Marcos Hernández](https://www.linkedin.com/in/optimiza/)), in collaboration with [MS-DOS Club](https://msdos.club) and its [podcast](https://www.ivoox.com/podcast-ms-dos-club_sq_f11160693_1.html).`
- One exception besides the credits line: the user-agent names of AI crawlers in `robots.txt`
  (`seo.CRAWLERS`), which a crawler announces about itself and which the file must spell to
  invite it by name. They are a program's name, not a mention of an assistant.
- Nothing else is exempt: a dated measurement, a note on the project's own history, a
  home-directory path in any tracked file, or an assistant's name in a tracked file outside
  `CLAUDE.md` and `.claude/`, is a finding.
