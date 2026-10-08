---
name: docinvariant
description: Review technical documentation for clarity, structural issues, and potentially meaning-changing revisions. Use for installation guides, API references, READMEs, procedures, runbooks, and security instructions. This is an evidence-limited audit, not ASD compliance certification.
---

# DocInvariant: technical-documentation review

Use the DocInvariant CLI in this repository (at `scripts/ste_audit.py`) when executable. When it cannot execute, clearly distinguish manual review from checker output. The skill is optional; the Python checker works independently of any LLM.

## Workflow

1. Identify the document audience, safety criticality, and whether each section is a procedure or description. Do not label every section identically just because the file is a procedure.
2. Record protected facts and tokens: actors, actions, objects, negations, authorizations, numeric thresholds, units, prerequisites, timestamps, code blocks, flags, filenames, paths, API names, warning labels and document structure.
3. Audit clarity and structural candidates. From the repository root run `python scripts/ste_audit.py YOUR_FILE.md --mode procedure --format json` (or `--mode description` for descriptive text).
4. If comparing revisions, add `--compare ORIGINAL_FILE.md`, carefully inspect all reported differences, and also manually inspect changed verbs, actor/object roles, permissions, action ordering, and omitted context. A zero-finding result is not proof of equivalence.
5. Prefer the smallest clear rewrite that preserves the original technical meaning. Never silently strengthen, weaken, or remove an obligation, authorization, requirement, condition, safety label, limit, or exception.
6. Report findings with locations, evidence, the check that produced them, and the required reviewer. Mark source facts versus inference and untested checks.
7. For a specific ASD-STE100 compliance question, consult a user-authorized copy of the official issue; do not infer lexical approval from ordinary English, pretend to check the full dictionary, or redistribute the source document.
8. Safety-critical or destructive instructions require a qualified subject-matter expert. Do not approve such text for operational use.

## Output contract

Provide (1) document classification, (2) executed versus manual findings, (3) proposed minimal changes, (4) semantic-risk ledger, (5) unknowns and human approval needs, and (6) precise tool limits.

**No affiliation, endorsement, certification, or full compliance is implied.**
