# DocInvariant

**Offline-first tools for reviewing technical documentation clarity and screening for meaning-changing edits.**

DocInvariant combines a deterministic Python CLI with an optional agent skill. It identifies *candidates* for human review; it does not establish correctness, semantic equivalence, or compliance with a standard.

> **Status: early research prototype.** This repository contains a partial structural checker, a limited protected-token change detector, and unit tests. Do not use its results as safety, security, operational, or standards approval.

## What it does

- Screens procedure and description sentences for approximate word limits.
- Flags possible passive constructions, semicolons, contractions, and selected condition-order patterns.
- Screens Markdown prose while skipping simple fenced-code blocks and tables.
- Compares drafts for changes to numbers, units, URLs, command literals, selected identifiers, obligation/negation words, and safety labels.
- Generates machine-readable JSON for local or CI review.
- Includes a portable agent-instruction skill at `skills/docinvariant/SKILL.md`.

**What it does not do:** detect every semantic reversal, parse the complete grammar, validate every dictionary entry, or prove that a rewrite preserves meaning. In particular, changing `Allow access` to `Deny access` and swapping actor/object roles can escape the current heuristic checker. See [known limitations](docs/known-limitations.md).

## Quick start

Requires **Python 3.10+**. The default scanner and token comparison have no external Python dependencies or network calls.

```bash
git clone https://github.com/amarjaleelbanbhan/docinvariant.git
cd docinvariant
python scripts/ste_audit.py examples/sample_procedure.md --mode procedure --format json
python -m unittest discover -s tests -v
```

To review a proposed edit against its original:

```bash
python scripts/ste_audit.py draft.md --mode procedure --compare original.md --format json
```

For an optional located **textual** revision screen:

```bash
python -m pip install -r requirements-comparison.txt
python scripts/ste_audit.py draft.md --mode procedure --compare original.md --compare-method blocks --format json
```

This mode reuses `markdown-it-py` and Python's `difflib`. It reports changed, added and deleted blocks with both file paths, inclusive line ranges and original source text. It retains inline-code values, fenced commands, links and tables, and ignores selected prose formatting changes. Dependency installation needs package access; comparison runs locally without fetching models or executing document commands. The default `--compare-method tokens` keeps the original behavior.

Block findings are textual differences requiring review, **not** verified changes in meaning. Harmless paraphrases, equivalent quantities and sentence splits can still alert. HTML and syntax omitted by the parser are reviewed as raw text. Inputs exceeding 200,000 characters or 2,000 blocks fail explicitly. See the [reproduced experiment](experiments/located_compare/README.md) for exact behavior and limitations. Install the optional requirements before running the full comparison tests; otherwise those tests are explicitly skipped.

Authored ordered-list numbers are compared even when CommonMark renders different later numbers identically. Numbering cleanup can therefore require review without changing rendered meaning. Delimiter/spacing style remains normalized. When duplicate normalized blocks accompany edits, `alignment_ambiguous` warns that `difflib`'s selected correspondence may not be unique; source ranges identify selected slices, not a proven deleted occurrence. Presentation changes to emphasis and soft/hard line breaks—including WARNING/CAUTION prominence—are normalized and are not assessed for safety. Table alignment, horizontal-rule style, Setext/ATX heading style, and indented/fenced code style are also normalized; whole-table evidence and numbered-list tail replacements can be broad. Use a raw diff when presentation, table alignment, or precise list renumbering matters. This is not an exhaustive raw-text diff.

The checker reads files without modifying them. The `--fail-on-length` option returns exit code 2 when it finds an approximate sentence-length issue. An exit code of 0 **is not a compliance or safety guarantee**.

## Source and research boundaries

This tool is informed by technical-writing principles, including **ASD-STE100 Issue 9 (January 2025)**, but **DocInvariant is not affiliated with, endorsed by, or certified by ASD or STEMG**. It does not distribute the ASD standard, copyrighted dictionary, or source PDF. Refer to the [publisher's official site](https://www.asd-ste100.org/) for the authoritative standard. See [standards, rights, and attribution](docs/standards-and-rights.md).

The current Python checker comes from the private Amar Jarvis STE Precision v0.4.0 prototype (checker version 1.2.0), separated from personal configuration. Research questions and benchmark proposals are in [research roadmap](docs/research-roadmap.md); **no benchmark performance claims have been established**.

## Project structure

```text
scripts/ste_audit.py         Offline read-only CLI
tests/test_ste_audit.py     Python unittest suite
skills/docinvariant/        Reusable instruction skill
examples/                  Fictional sample input
docs/                      Architecture, limitations, research, rights
.github/workflows/          Automated unit tests
```

## Safety and contributions

DocInvariant can miss dangerous meaning changes. It is not intended to approve live procedures or rewrite security requirements unattended. Please read [SECURITY.md](SECURITY.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

Code and original repository materials are available under the [MIT License](LICENSE); **this does not license third-party standards or trademarks**.
