# First audit in 10 minutes

This walkthrough shows what DocInvariant flags on a meaning-changing edit, and what it *cannot* verify. You need **Python 3.10+** and a clone of this repository. No extra packages.

> DocInvariant is **not endorsed or certified by ASD/STEMG**. Findings are review candidates, not proof of a writing-rule violation, semantic difference, or STE compliance.

## 1. Run a single-file screen

From the repository root:

```bash
python scripts/ste_audit.py examples/sample_procedure.md --mode procedure --format json
```

You should see JSON with `review_status`, `findings`, and a `limitations` list. Structural findings are *candidates*; they are not proof that a writing rule was broken.

## 2. Compare a proposed edit against the original

Two small fictional samples live under `examples/`:

- `examples/meaning_change_original.md` — obligation `must` and threshold `5`
- `examples/meaning_change_proposed.md` — obligation `should` and threshold `10`

Run:

```bash
python scripts/ste_audit.py examples/meaning_change_proposed.md --mode procedure --compare examples/meaning_change_original.md --format json
```

Look at `comparison.protected_token_changes`. You should see at least:

- `numeric_units`: `5` removed, `10` added
- `modal_polarity_condition`: `must` removed, `should` added

A **protected-token change** is a reason to request human review. It is **not** proof that the documents mean different things. Harmless edits can change tokens; harmful edits can leave tokens unchanged.

## 3. Interpret a quiet result honestly

An empty `findings` list means no structural candidates were reported. When comparing files, also inspect `comparison.protected_token_changes`. Exit code `0` means the command completed, **not** that the audit passed or that the documents match. Neither a quiet result nor exit code `0` guarantees:

- safety or operational correctness,
- semantic equivalence between drafts, or
- official ASD-STE100 compliance.

See [known limitations](known-limitations.md) for cases the heuristics miss.

## 4. Confirm the unit tests still pass

```bash
python -m unittest discover -s tests -v
```

## Concepts in one line each

| Term | Plain meaning |
| --- | --- |
| Structural finding | A heuristic match that merits a look — not proof of a rule breach |
| Protected-token change | A number, obligation word, URL, or similar token changed — ask a human |
| Zero findings | The screen stayed quiet — not a safety or equivalence certificate |

## Next steps

- Read [architecture](architecture.md) if you want to extend the checker.
- Advanced tasks: semantic reversals (#1), NOTE checks (#2), research benchmark (#3).
