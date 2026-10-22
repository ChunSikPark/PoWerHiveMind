---
description: Write a new page into this knowledge base, or check that the pages already here still hang together
---

# Knowledge base page

Grow this knowledge base. A session that worked something out and left it in the
chat has thrown it away.

Invoke the `knowledge-base-page` skill and follow it. It carries the filing
tree, the page shape, the link rules and the `index.md` bookkeeping.

Two things are easy to skip and are the whole point:

1. **Search before you write.**
   `grep -rn -i "<term>" concepts/ methods/ references/ demos/` on both the
   plain-English phrasing and the identifier. If a page already covers it, edit
   that page. A second page on one topic is the failure this base exists to
   avoid.
2. **Add the `index.md` row.** One row, in the table for the page's folder. A
   page nobody can find is a page nobody reads.

## If they asked you to check the base rather than add to it

Run the first two snippets at the end of the skill. One lists pages missing an
`index.md` row, the other lists links pointing at files that do not exist.
Paste what they print. Both returning nothing is the healthy state.

Report what you found. Offer to fix it; do not start rewriting pages unasked.

## Before you claim any of this is done

Show your work. Paste the search you ran and the output of the checks. "It
looks right" is not evidence, and both checks are one command each.
