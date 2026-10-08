# Architecture (research prototype)

## Data flow

Input Markdown/text -> conservative prose extraction -> approximate sentence/paragraph screening -> structured candidate findings.

Optional second input -> protected-token multiset differences + nearby modal-context windows -> mandatory manual review where differences are flagged.

Opt-in `--compare-method blocks` -> markdown-it-py CommonMark AST with table support -> ordered block keys and source maps -> stdlib `difflib.SequenceMatcher` opcodes -> raw old/new source ranges for manual review. This is a textual diff adapter, not sentence alignment or a semantic classifier. Unsupported HTML/AST gaps remain raw reviewable text; parsing and diffing have explicit size bounds. The structural scanner remains separate and unchanged.

The CLI reports separate `review_status` and `lexical_status` values. Findings identify a probable issue, not a verified violation.

## Implemented checks

Approximate sentence length (procedural and descriptive), basic notes, semicolon usage, contraction candidates, simple passive patterns, limited prerequisite-order patterns, descriptive paragraph size, number/unit patterns, URL and inline literal changes, known identifiers, safety label changes, and modal/negation differences.

## Boundaries

The code uses regular expressions and a simple Markdown extractor. It is neither a full parser nor a semantic model. It cannot tell whether an API call is safe or a procedure is accurate, and does not have a licensed controlled dictionary. It can miss altered verbs and swapped agents/patients even when tokens are unchanged.

The checker version (`1.2.0`) differs from the original Amar Jarvis plugin version (`0.4.0`), and from future DocInvariant releases.

## Design constraints

The default flow uses Python's standard library only. Located block comparison has an optional, pinned MIT parser dependency and its MIT URL helper. Both flows execute locally, without file mutation or document command execution, and produce deterministic findings with explicit failures. Future semantics work should remain opt-in; any LLM-assisted judgment must be disclosed and benchmarked separately.
