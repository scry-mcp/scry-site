# Decisions

Why the site shows the knowledge base the way it does. Each section is one decision, its reason,
and the date it was taken; the code and the checks are what keep it true.

## 2026-11-28: the example is regenerated whole

`knowledge_find`'s example is copied from `docs/reference/examples.json`, which each server writes
from a real run, never typed into a page by hand. The site emits it unchanged.

A hand-written excerpt drifts: the reply's fields are the server's to change, and an example
carried here would keep answering the question it used to. Regenerating it makes the page quote
the server, and a build that finds the example is not one named entry stops instead of drawing
something else.

## 2026-11-28: a knowledge reply is never truncated

The whole reply goes on the page as the server answered it. No text of the base is cut, and the
only thing dropped is the pair of fields that count what the base holds (`served`, `held_back`)
together with the reading sentence that only counts them, because a public page says what the
base answers and not how it is being filled.

A reader who opens the reply sees rows, cites and the emulator's verdicts. Cutting them would
hide exactly what the entry is for, and a page that says it holds the whole reply must hold it.

## 2026-11-28: the sections are called `Symbols` and `Knowledge`

The family that looks a name up is `Symbols`, and the one that asks the base what a number is is
`Knowledge`. Both were once `Names`, which named an effect and left the reader to work out what
the section held.

The site reads the family names from each server's `REFERENCE.md` index and never writes one of
its own, so these names, and any later rename, reach the pages without a change here.

## 2026-11-28: the families both servers share come first

Both servers list the families they have in common first, in the same order, and each server's
own afterwards. The site keeps the order each `REFERENCE.md` index gives.

A reader who has learned where `Symbols` and `Knowledge` sit meets them in the same place on the
other server, and the families that only one emulator has do not come between them.

## 2026-11-28: a reply longer than the pane goes whole in a closed `<details>`

An example's reply is drawn in a pane, which every visible code block of the site limits. When
the reply is longer, the pane keeps an excerpt of a few lines and the whole reply follows under a
`<details>` closed on arrival.

The pane is the shape of the reply; the `<details>` is the reply. A reader who only wants to see
what comes back reads the pane, and one who wants a particular row opens the whole and finds it
there. The pane carries how many fields it shows of how many the reply has, so the two are never
mistaken for each other.
