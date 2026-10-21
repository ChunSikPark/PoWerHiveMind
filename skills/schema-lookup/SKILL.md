---
name: schema-lookup
description: "Answer which PowerWorld object, field or SCRIPT command to use, and show what HiveMind's study pages say about it. Use when the user asks which field holds something, what the key or required fields of an object are, how to set an option (iterations, island reporting, SCOPF loops, DC mode), what a field or concise name means, or whether a field exists at all - e.g. 'which parameter do I set for...', 'what fields does a shunt need', 'is there a setting for...'."
topic: agents
---

# Schema lookup

Answer from HiveMind's own sources, never from memory. PowerWorld has about 1,000 object types
and 100,000 fields; a guessed field name fails silently.

## 0. The kit root

Installed as a Claude Code plugin, `${CLAUDE_PLUGIN_ROOT}` in this file is replaced with HiveMind's
absolute path before you read it, so the commands below run as written. It is **not** an
environment variable: in any other harness, or if you still see the literal text
`${CLAUDE_PLUGIN_ROOT}`, type the absolute path of the directory holding `AGENTS.md` in its place.
A bare `skills/...` path runs against the user's working directory and fails.

## 1. Look it up

```
python "${CLAUDE_PLUGIN_ROOT}/skills/schema-lookup/engine/lookup.py" object <Object>
python "${CLAUDE_PLUGIN_ROOT}/skills/schema-lookup/engine/lookup.py" field <Object> <Field>
python "${CLAUDE_PLUGIN_ROOT}/skills/schema-lookup/engine/lookup.py" search "<words>" [--object <Object>] [--limit 10]
```

- Don't know the object? `search` without `--object`, then `object` on the best hit.
- A field may be given by variable name (`DCPFMode`), concise name (`DCApprox`) or Python
  spelling (`MaxItr__1`); all resolve to one field.
- Exit 2 with "pip install openpyxl": tell the user to run it (or `/powerworld-hivemind:powerworld-setup`).
- Otherwise, relay any other exit-2 message verbatim.

## 2. Read what the tool printed about the hub

`field` prints the rows of `references/powerworld-study-options.md` that name the field, verbatim:

- `[exact]` rows name `Object.Field` — they are about this field.
- `[name]` rows only mention the bare name and **may concern another object**. Read the row before
  using it.
- The row's words decide the answer. A row that says **decoy** or **trap** overrides everything else;
  the tag (`V` verified on a live case, `D` documented, `S` schema only) rates the row's claim.
- A row marked `paragraph` is prose from the hub that names `Object.Field`; quote it the same way.
- No hub rows: say "field export only — PowerWorld describes it; its behaviour is untested here".

For exact SCRIPT syntax and defaults, read `${CLAUDE_PLUGIN_ROOT}/references/powerworld-study-commands.md`,
including its "Surprises" section before recommending any command.

## 3. When the field does not exist

Exit 1. The tool prints **spelling neighbours — not substitutes** — and the hub passages that match
the words of the request. Offer a real alternative only if a hub passage names it (e.g. "no SCOPF
inner loop; the per-LP limit is `OPF_MaxLPIterations`"). Never present a spelling neighbour as the
answer.

## 4. Answer in this shape

```
<Object>.<Field>  (concise: …)      type · writable · role (key 1 / required / -)
what it does: <one line, from the description>
how to set it: SetData(<Object>, [<Field>], [<value>]);   — then read it back
the kit says: <the hub row, quoted, with its tag> | field export only
```

The `how to set it` line depends on `writable`: yes — as above; aux-only — only from an aux file;
edit-mode — only in EDIT mode; depends — say so and quote the export's condition;
read-only: say it cannot be written, and give no SetData line.

For "what do I need to create an X": the keys in order and the required fields.

## Never

- Never open, solve or write a case; never run anything but this CLI and read-only commands.
- Never state a field that the tool did not return.
- Never summarise a hub row into a confidence word; quote it.
