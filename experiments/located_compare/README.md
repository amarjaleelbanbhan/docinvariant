# Located Markdown comparison: engineering evidence

Status: **REPRODUCED engineering probes**, not independently human-labeled research or evidence of user demand. Fixtures are original, authored with model assistance, and included under the repository MIT license. No ASD text, private documents or model weights are included. Intended `changed`/`preserved` labels describe test design, not independent adjudication. Claude's E1 benchmark still needs two independent human labellers.

## Reproduce

From the repository root, Python 3.10+:

```bash
python -m pip install -r requirements-comparison.txt
python -m unittest discover -s tests -v
python experiments/located_compare/run.py --output /tmp/located-comparison.json
```

The comparison runner uses Git to load the exact original checker from `dada59452ad4b18cb43e23619650d240edcea1eb` without modifying it, and runs ordinary GNU `diff` plus stdlib `difflib`. Use a checkout containing that commit (not a shallow clone omitting it). GNU diff must be installed. The runner blocks Python sockets during comparisons and never executes fixture commands. It is a small reproduction script, not a new evaluation framework; it reports counts rather than semantic metrics or inferred labels.

These reproduction commands and the GNU-diff runner are Linux/POSIX-oriented, with `/tmp` paths and external Git/diff prerequisites. That is separate from the local CLI's Python 3.10+ support. Windows CLI execution was not independently tested here.

To include the existing Semantic Change Radar implementation:

```bash
git clone https://github.com/Habetyan/semantic-change-radar.git /tmp/semantic-change-radar
git -C /tmp/semantic-change-radar checkout --detach 708083d99b77de721a8e1302fbd4190a20129a42
python -m pip install numpy==2.3.5 scipy==1.17.0
python experiments/located_compare/run.py --output /tmp/located-comparison-with-radar.json --radar-source /tmp/semantic-change-radar
```

The listed NumPy/SciPy versions reproduce the Python 3.12.14 environment used here; this optional competitor setup is not part of DocInvariant's dependencies or its Python 3.10 compatibility promise. Radar's lexical path imports NumPy/SciPy; UI/model packages and weights were not needed for these runs. Its `baseline` profile and exact code SHA are recorded in `results.json`. Full findings, opcodes, commands, fixture hashes and versions are retained there.

## Observed counts

28 small, deliberately constructed regression pairs; 17 intended consequential revisions and 11 intended harmless controls. No holdout, independent human gold, power calculation, or general accuracy claim.

| Method | Consequential fixtures exposed / 17 | Harmless controls alerted / 11 |
|---|---:|---:|
| GNU diff 3.10 (`diff -u`) | 17 | 10 |
| stdlib difflib | 17 | 10 |
| Frozen DocInvariant 1.2.0 | 4 | 4 |
| Markdown block diff | 17 | 5 |
| Radar lexical, baseline profile | 17 | 7 |

The deletion fixture uses bullets to avoid incidentally detecting renumbered steps rather than the verification omission. Exposed revisions include authorization reversal, actor swap, swapped quantity owners, deleted verification/prerequisite, code-path swap, fenced command, sign, unit, condition, exception, obligation, quantifier, link and table edits. This is **textual exposure**, not correct semantic classification. Baseline token equality misses 13 of these constructed cases.

Block mode suppresses soft wrapping, emphasis, fence delimiter style, bullet marker style and blank-line changes in this fixture set. It still alerts on all five intended semantic-preservation controls involving negation paraphrase, unit equivalence, number separators, synonyms and sentence splitting. It is not automatically useful merely because it exposes every consequential test revision. Radar also exposes all 17; lower counts on these five formatting examples do not establish superiority.

The first block comparison took ~14.90 ms including initial parser import; median across 28 cases was ~0.54 ms in this recorded run. This is not a production performance benchmark. Parser/helper target installation occupied approximately 976 KiB here, excluding Python/runtime and installer overhead.

## Reuse decision and rights

- `difflib.SequenceMatcher` supplies existing opcodes; no new matching algorithm or move detector is implemented. `autojunk=False` preserves repeated short instructions; size limits bound worst-case work.
- `markdown-it-py` 4.0.0 and `mdurl` 0.1.2 have MIT LICENSE text in their installed distributions. The parser is optional and only loaded for block comparison. Its CommonMark preset correctly handles four-backtick fences, prose soft wrapping and source maps; the enabled table rule retains cell order.
- Radar's actual `compare.py`, `structure.py`, grouping/detail code, license and scorer were inspected. Its lexical backend is reusable MIT code and already exposes these edits. Its custom regex segmentation, additional numerical runtime dependencies, and formatting alerts led to a smaller Markdown AST-to-stdlib-diff adapter for this bounded CLI flow. No Radar code, dataset text or model is copied into DocInvariant. This is not a novelty claim; upstream contribution remains an option after real-user evaluation.
- ste-cli 0.10.1 and Vale 3.24.0 with the inspected STE styles were previously executed for structural checks. They do not supply the pairwise task through the inspected interfaces. No structural reimplementation or migration is included here.
- Parser source audit: markdown-it-py `6f586542653a56d2ee8549a0dccfaa6ba5ebe14a`; installed runtime 4.0.0. These are different snapshots. Selected block/inline rules, licenses and table behavior were inspected before use. No model/dictionary/data asset is integrated.

## Independent reproduction of a Radar artifact

`radar_reproduction.json` records a separate execution of the upstream `evaluation.real_evaluate` runner against `evaluation/blind-v3/manifest.json`, lexical backend and baseline profile, on commit `708083d99b77de721a8e1302fbd4190a20129a42`. All metric dictionaries, failure counts and source hashes exactly match its committed `artifacts/evaluation/v3-blind-lexical-baseline/summary.json`. Six document pairs ran without failure. No weights or semantic backend ran.

Executable reproduction after the optional competitor setup above:

```bash
cd /tmp/semantic-change-radar
HF_HUB_OFFLINE=1 python -m evaluation.real_evaluate --backend lexical --profile baseline --manifest evaluation/blind-v3/manifest.json --output /tmp/radar-v3-lexical
```

The recorded local run additionally blocked Python sockets via a wrapper; outputs record Python/NumPy/SciPy versions. To compare, load both summary files with Python/json and compare their `metrics`, `failed_cases`, and `source_hashes`. Timing/creation dates are expected to differ. Execution reproduction does not validate the AI-assisted/author-confirmed reference labels. Its conditional and end-to-end metrics are different; the blind lexical artifact itself records one risky miss. Historical real/synthetic runs and all model runs remain unexecuted here, so their reported measurements are not used as evidence of our method's accuracy or model value.

## Failure-driven fixes and limits

Two additional formatting failures were found after the first passing suite: Setext underlines were initially treated as unmapped text, and an unused reference's terminal newline alerted. Heading parent maps and newline-only fallback normalization fix those cases with regression tests. Table padding, code emphasis, duplicate deletion, HTML, image/link targets, source-map ranges, missing dependencies, empty inputs and size failures have regression coverage.

Default structural checks and protected-token comparison are unchanged. New findings use `semantic_status: NOT_ASSESSED`; zero findings cannot establish equivalence or safety. Replacement groups are diff hunks, not asserted proposition/sentence matches. Moves, splits, merges, synonyms and quantity equivalence may require review. CommonMark inline syntax is decoded by the parser; prose whitespace/emphasis are normalized, code values remain in ordered keys, and raw source is included for each reported side. Nested markup ownership is retained, but role/quantity binding is not inferred. HTML, unused definitions and other unmapped source are literal comparisons; embedded syntax is not analyzed.

Maximum input: 200,000 characters and 2,000 blocks per side. Over-limit input fails explicitly rather than silently truncating. Python package installation can access the network; document comparisons do not fetch resources. CI tests dependency-free/default behavior first, then the full optional suite on Python 3.10–3.13. Rollback: keep using default token mode or remove the optional adapter. Independent human labels and real documentation-review usefulness remain the next research blockers.

## PR review corrections (P1/P2)

Both cases reproduced on the pre-review adapter `496662174ee4811cefc310b31845f96dd652fa89` using pinned markdown-it-py **4.0.0**. The original 28 fixtures, `results.json`, and `radar_reproduction.json` are preserved. `results_after_review.json` contains a new run on the same 28 inputs; all five arms' alert counts are unchanged. `review_fixtures.json` and `review_results.json` retain ten separate targeted probes, including before/after adapter outputs. These are regression fixtures, not E1 human labels; they must not be combined into a research score.

P1: `1. Restart service. / 2. Delete backup.` versus later marker `9.` initially produced no finding. The parser's `list_item_open.info` retains every authored ordered number, while CommonMark rendering uses only the first number as the list start. The adapter now reuses this field in the container key. No Markdown lexer/parser or alignment algorithm was added. The changed item is reported on line 2 with exact old/new source. Nested numbering is covered too. Starting-list changes affect rendering and also alert; `.` versus `)` and harmless spacing do not alert. The `1., 1.` → `1., 2.` cleanup renders identically but now deliberately alerts: authored numbering/cross-reference review is the policy, not a claim that rendering or meaning changed.

P2: identical repeated instructions previously produced a deterministic selected deletion with no uncertainty indicator. Findings involving repeated normalized keys now carry `alignment_ambiguous: true`. A report-level flag and coverage note conservatively warn whenever edits coexist with duplicate keys, including duplicates outside a particular changed hunk. This is an ambiguity indicator, not a calibrated probability or proof that every flagged match is non-unique. `false` does not prove general alignment correctness. Exact original/proposed spans remain intact and the `difflib` opcode algorithm is unchanged. Unchanged repeated documents produce no edit finding; unique deletion does not raise this duplicate warning.

Normalization also applies to WARNING/CAUTION emphasis and line-break presentation. A targeted test confirms that presentation-only changes can yield no revision finding with `semantic_status: NOT_ASSESSED`. Visual prominence and safety presentation are outside this mode's coverage; ordinary diff remains appropriate when reviewing every markup edit.

| Targeted probe group | Pre-review block adapter | Corrected block adapter |
|---|---|---|
| 6 intended edits | 4 exposed | 6 exposed |
| 4 intended preserved controls | 0 alerted | 1 alerted (render-equivalent renumbering) |
| Duplicate deletion | Selected source occurrence, no ambiguity field | Same deterministic selection, explicit ambiguity |

Ordinary diff/difflib expose all six targeted edits and alert on three preserved controls; the frozen checker exposes three/alerts on two; Radar lexical baseline exposes four/alerts on one. Radar misses later authored-marker and list-start changes in this targeted set. These counts describe normalization/detection policies on constructed inputs and do not demonstrate semantic superiority. The original block-mode five harmless alerts remain unresolved.

Reproduce from the repository root (after the optional Radar setup above):

```bash
python experiments/located_compare/run.py --output /tmp/review-results.json --fixtures experiments/located_compare/review_fixtures.json --previous-block-ref 496662174ee4811cefc310b31845f96dd652fa89 --radar-source /tmp/semantic-change-radar
python experiments/located_compare/run.py --output /tmp/results-after-review.json --radar-source /tmp/semantic-change-radar
```

## Corrected upstream interpretation

Read [Claude's Issue #7 update](https://github.com/amarjaleelbanbhan/docinvariant/issues/7#issuecomment-6070149501). Claude reports dev/test lexical results reproducing metric-for-metric, with a historical `compare.py` source hash absent from committed history. These dev/test executions/history searches were **not repeated here**. Independently reading the artifacts confirms their recorded `compare.py` hash differs from current source. The separately reproduced **blind-v3** lexical run retained here has matching source hashes; this scope must not be conflated with historical dev/test provenance.

Independently inspected `_classify()` confirms that the lexical backend marks every nonidentical aligned passage as modified without a semantic decision. Recall on eligible aligned edits largely follows that alert policy; alignment, normalization, omissions and coverage can still cause end-to-end misses. The targeted marker misses illustrate why “perfect recall by construction” must not be generalized to all raw edits. Neither Radar nor this adapter discriminates consequential changes simply by surfacing them. Reproducing a computation does not validate its task labels.

All cited upstream labels are AI-authored or AI-reviewed and not independently human-validated. The annotation-provenance note's author confirmation is not independent adjudication or human gold. Model-generated references cannot support a DocInvariant accuracy claim. Claude's real-corpus and rights work remains separate and ongoing; no new corpus/model/data dependency was adopted, and no real-corpus rights or semantic-model benefit is claimed here. Models remain deferred for this focused PR because the implementation scope is textual review, not because lexical scores prove semantic adequacy.
