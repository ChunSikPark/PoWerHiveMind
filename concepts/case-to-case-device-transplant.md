---
type: concept
domain: cross-cutting
topic: design
aliases: [AUX transplant, device delta transplant, LoadAux create]
tags: [powerworld, esapp, aux, technique, case-diff]
---

# Case-to-case device transplant

## Abstract

How to copy a set of devices from one PowerWorld case into another without rebuilding the chain
that produced them — useful whenever a feature was developed on one scenario and the others are
stranded behind unscripted stages. Carve a **filtered AUX out of the source case's own
`SaveCase(AUX)` dump** so the field lists are PowerWorld's rather than hand-written, and load it
with `LoadAux(create_if_not_found=True)`. To *move* a device between buses, carve its record out
of the **target** case and re-point the bus number, so the whole schema transfers by construction.
Proven 2026-09-01 on four Synth9k scenarios: hundreds of buses, over a thousand shunts, about a
thousand branches, hundreds of gen moves, over a hundred load moves, criterion-10 clean on all four.

## Connections

- Used in a study spanning several scenarios, to answer an accepted migration risk.
- Complements [comparing-planning-cases](../demos/comparing-planning-cases.md) — that is about *reading* a diff across two model
  vintages, this one is about *applying* one.
- Depends on the same key-field constraint as renaming a branch's circuit ID: some fields can only be changed
  through an AUX text round-trip, never by a write.
- 💡 **Could transfer to:** any study where one scenario got a
  feature and the rest need it, or where a chain is unreproducible and only the *result* survives.

## Content

### The method

1. `SaveCase(AUX)` the **source** case. Its per-object blocks (`Bus (…) { … }`) carry PowerWorld's
   own complete field lists — never hand-write one, and never assume a field name.
2. Keep only the records you want, by key. Watch for **duplicate blocks**: a full dump writes
   `Bus`, `Gen`, `Load` and `Branch` more than once (the extras carry cost / OPF fields). Filter
   every occurrence, not the first.
3. Write them back out ordered **Bus → Shunt → Branch → Transformer** so references resolve.
4. Load into the **target** with `LoadAux(path, create_if_not_found=True)`.

### The trap that eats an hour

**`ProcessAuxFile` on a data aux creates nothing and reports success.** No error, no warning, and
the device counts are simply unchanged. `LoadAux(..., create_if_not_found=True)` is the working
call; the create flag is the entire difference. Assert on device counts after the load, never on
the absence of an exception — a discipline guards that report evidence they did not gather
argues for generally.

### Moving a device between buses

There is no move operation. Delete-and-recreate risks dropping fields silently — the
`LoadGrounded` bug hit every moved load in the original migration and was invisible to a diff over
the write set, because a dropped field is by definition absent from it.

**Carve the record out of the TARGET case's own aux and re-point only the leading bus-number
token, then delete the original.** The whole schema then transfers by construction: there is no
field list to get wrong, and no value from the source case can leak in. This is what makes the
technique safe across scenarios — a moved generator keeps *its own* scenario's dispatch, not the
donor's.

### Always undo the text rounding

The aux writes R/X/C to 6 decimals and MW / limits to 3. Snapshot exact values before the
round-trip and write them back afterwards, confirming on read-back. Skipping this left the moved
loads 7.3e-3 MW light — small enough to pass a loose tolerance and wrong enough to poison a
conservation check later.

### esapp notes

- esapp has **no `change_and_confirm_params_multiple_element`** (the older `esa` package does).
  Write with `ChangeParametersMultipleElement`, then read back and compare yourself.
- `GetParametersMultipleElement` returns **`None`**, not an empty frame, for an object type with
  zero instances — a case with no shunts will crash a naive `len()`.
- See [esapp](esapp.md) and the `SaveCase` script-command trap: `pw.save()` writes nothing silently.

### When the numbering cooperates, check for it first

The Synth9k transplant needed **no renumbering at all**, because the target's highest bus number
sat below every new bus number in the source, which formed one contiguous block above it. That is worth two minutes of checking before
designing a remap: disjoint ranges turn a hard problem into a copy.
