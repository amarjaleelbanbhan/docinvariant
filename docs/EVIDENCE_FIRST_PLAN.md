# DocInvariant — Evidence-First Project and Research Plan

**Status:** planning only, not a feature implementation commitment.  
**Established:** 2026-10-09. **Owner:** Amar Jaleel. **Project:** https://github.com/amarjaleelbanbhan/docinvariant

## 0. Non-negotiable operating contract

- **Reuse before build.** Before proposing any new parser, linter, NLP pipeline, model, visualization, runner, or CI integration, search for maintained existing implementations; test the best candidate on the exact task. Write only a justified missing adapter or missing detection capability.
- **Evidence before claims.** Label every statement `VERIFIED_SOURCE`, `REPRODUCED`, `HYPOTHESIS`, `UNKNOWN`, or `DECISION`. A passing test validates that test, not a claim of overall accuracy or standards compliance.
- **No invention.** Never invent user preferences, license permissions, empirical results, metrics, citations, adopters, novel contributions, or sources. Distinguish third-party claims from independently reproduced measurements.
- **No unsafe auto-fix.** Source text is read-only by default; no unattended rewriting of security, safety, deletion, permission or operating instructions. A human reviews any meaning-critical change.
- **No proprietary standards redistribution.** Do not commit the ASD-STE100 PDF, its dictionary, protected examples or copied rule text. DocInvariant is not affiliated with, endorsed or certified by ASD/STEMG. Obtain authoritative references through the publisher.
- **Privacy first.** No default uploading, telemetry, credential processing, or collection of private manuals. An optional model/cloud integration needs explicit consent and a clearly separated mode.
- **Small diffs, independent review.** New contribution must cite its purpose, existing alternatives, cost, reproducer, tests, rollback, negative cases, and reviewer.
- **Do not claim research novelty or practical demand without evidence.** The paper must be based on experiments; negative results are valid results.

## 1. Verified starting point (not forecasts)

The public repository currently has a Python 3.10+ offline regex-based checker (v1.2.0), 49 unit tests, a portable skill, CI, documentation, and open issues. It is a partial structural scanner plus a narrow protected-token change screen. Known misses include:
- `NOTE: You must delete the backup file.`
- `Allow user access.` -> `Deny user access.`
- `The server sends data to the database.` -> `The database sends data to the server.`

These are known cases documented in `docs/known-limitations.md`; they must be reproduced again under the current commit before changes. Current test count is *not* an accuracy result.

### Evidence that the wider problem is real

Uddin and Robillard's study *How API Documentation Fails* (IEEE Software, 2015, DOI:10.1109/MS.2014.80) examined developer-reported documentation failures; ambiguity, incompleteness and incorrectness were prominent: https://www.cs.mcgill.ca/~martin/papers/ieeesw2015.pdf

This is evidence that developers experience documentation problems. It does **not** demonstrate demand for our specific product, nor that DocInvariant solves them.

## 2. Existing tools — candidate reuse inventory (provisional)

| Need | Existing candidate | Verified upstream link / license evidence | Status |
|---|---|---|---|
| Markup-aware prose linting | **Vale** | https://github.com/vale-cli/vale (MIT) | Primary candidate; evaluate before extending own parser |
| Alternative Markdown lint rules | **textlint** | https://github.com/textlint/textlint (MIT, Node.js) | Compare tool ecosystem and installation burden |
| Existing STE mechanical checks | **ste-cli** | https://github.com/TudorAndrei/ste-cli (MIT per repo) | Mandatory direct baseline; assess issue/version and output |
| Existing STE skill/checker | **ste100** | https://github.com/Kopachelli/ste100 (MIT per repo) | Mandatory direct baseline |
| Existing Vale STE rules | **vale-ste** | https://github.com/amoslives/vale-ste (MIT per repo) | Check scope and 20/25-word distinction |
| Other STE linter | **stuffbucket/vale** | https://github.com/stuffbucket/vale (MIT per repo) | Compare; do not confuse with vale-cli/vale |
| Offline sentence/dependency parsing | **spaCy** | https://github.com/explosion/spaCy (MIT library) | Optional if deterministic rules prove insufficient |
| Existing grammar proofreading | **LanguageTool** | https://github.com/languagetool-org/languagetool (LGPL-2.1-or-later core) | Optional comparator; check integration/license costs |
| PR annotations | **reviewdog** | https://github.com/reviewdog/reviewdog (MIT) | Reuse instead of creating own GitHub bot |
| Cross-tool results | **SARIF** | https://sarif.info/ (OASIS standard) | Consider only if interoperability is needed |

These projects have been found and inspected at README/docs level; **we have not yet benchmarked or integrated them**. Before adoption, record dated release/commit, verified effective license (including bundled rules/models), dependency weight, install support, offline behavior, maintenance, and observed results.

**Critical scope distinction:** Original ASD-STE100 Issue 9 controlled dictionary is not open-source. Free personal access is not permission to redistribute. MIT project code does not extend MIT rights to third-party data, models, style packs, or documentation.

## 3. Research protocol — how we avoid AI research mistakes

### R1 — Exact question
Ask falsifiable narrow questions: `Can an existing checker flag problem X?`, `Can an offline parser recognize a changed agent/patient role?`, `What do humans mark as a risky edit?`. Do not start with a desirable answer.

### R2 — Primary source chain
For every candidate: upstream repository -> exact release/commit -> LICENSE and model/data cards -> source and tests -> executable reproduction. For academic claims: original paper, venue, DOI, stated dataset/protocol. Record access dates. Search for contradictory results and limitations.

### R3 — Evidence log
Record `claim_id | claim | evidence URL + exact location | inspected version | method | VERIFIED_SOURCE/REPRODUCED/HYPOTHESIS/UNKNOWN | contradiction | owner | date`. Do not promote a source author's claim to independent verification.

### R4 — Stop before building
A feature request requires (a) a user/problem case, (b) an explicit check of existing alternatives, (c) a minimal failing fixture, (d) user benefit to test, and (e) why configuration/adaptation cannot solve it. If not established, mark `research-only`.

### R5 — Copyright/license/privacy gate
Read effective LICENSE/NOTICE and dependencies; separate `free to download`, `open-source`, `commercially usable`, and `redistributable`. Review local inference models separately from the libraries running them. No official standard pages/dictionary in the repository. Seek legal review for unclear redistribution/commercial use.

### R6 — Experimental hygiene
Freeze baseline before changes; predefine metrics and examples; maintain separate development and untouched holdout sets; split by originating project/template so near-duplicates do not leak. Keep gold labels independent of the system being assessed. Log tool and model versions, prompts, model settings, seeds where meaningful, hashes, environment, runtimes and failures.

### R7 — Independent evaluation and critique
Two independent human raters label a pilot sample; reconcile disagreements and preserve disagreement logs. LLM assessment can be an *additional measured baseline* and never the gold standard. LLM judges have documented position/verbosity biases: https://arxiv.org/abs/2306.05685

### R8 — False-negative/false-positive balance
Include unsafe edits (negation, quantity, permission, agent/object, precondition, omission) and harmless edits (wording, equivalent phrasing, reordered but equivalent prose). Count both missed dangerous changes and alerts on safe changes. Never label `no findings` as safe.

### R9 — Make results actionable
Every finding: path/line(s), original and revised span, detected risk category, tool/source/version, evidence, confidence limitation, reason for SME review, and proposed user action. No arbitrary numerical confidence score.

### R10 — Honest reports
Separate *structural language quality*, *semantic change*, *technical correctness*, and *ASD compliance* into different evaluation tasks. Vale's style linting must not be scored as a failed semantic checker unless it is explicitly configured to perform that task.

### R11 — Reproducibility
Maintain executable scripts and immutable experiment manifest; provide `make`/Python commands only after tested. Prefer stdlib for core and optional adapters for heavier dependencies. Report incomplete or unsuccessful experiments without hiding them.

### R12 — Anti-overengineering budget
No website, hosted service, database, vector store, autonomous agents, custom NLP model, or integrated browser extension until a measured case cannot be solved by a documented CLI + existing tool. Keep both runtime and maintenance costs visible.

## 4. Phases and stop/go acceptance criteria

### Phase A — Foundation and independent tool audit (FIRST)
1. Pin repo baseline and reproduce reported misses on the published commit.
2. Build an alternatives matrix: Vale, textlint, ste-cli, ste100, vale-ste, stuffbucket/vale, spaCy, reviewdog.
3. Run an **identical permitted fixture set** across relevant candidates; save commands, environments, full outputs and license proof.
4. Identify whether a Vale ruleset + existing STE tool completely covers our structural requirements.
5. **Gate A:** Choose reuse/configure/wrap/build separately for each function. Do **not** migrate until measured evidence favors a candidate.

### Phase B — Problem-validation and gold pilot
1. Interview or collect consented feedback from developers/docs maintainers. Do not invent user stories.
2. Create a *pilot* set of about 60–100 original/license-safe instruction pairs, balanced across harmless and harmful edits. The size is a trial target, not a statistical-power justification.
3. Two reviewers separately mark `preserved / changed / unclear`, the affected proposition, error class, severity rationale and textual evidence. Reconcile disagreements.
4. Preserve an untouched holdout group split by project/template; forbid manual tuning on holdout.
5. **Gate B:** If potential users do not find the detected mistakes useful, narrow or stop the feature instead of expanding it.

### Phase C — Reuse-first technical prototype
1. Keep original offline CLI functional as baseline.
2. Trial Vale for markup-aware linting instead of writing our own parser. Check license and release compatibility.
3. Trial smallest existing parsing component (spaCy only if needed) to extract agent/action/object/negation/scope differences. Parse uncertainties must be surfaced, not guessed away.
4. Introduce **only** narrowly justified missing checks with counterexamples and regression tests.
5. Integrate reviewdog only if users need PR annotations. No automatic high-risk fixes.
6. **Gate C:** Show added detection on held-out types without unacceptable false-positive growth and without replacing a mature tool unnecessarily.

### Phase D — Controlled comparative evaluation
Separate tasks:
- **Structural:** current DocInvariant, candidate Vale/rules, direct STE tools; precision/recall of correctly labeled *structural* issues with officially supported rule interpretations where applicable.
- **Meaning-change:** naive textual diffs; current protected-token screen; reuse-first pipeline; optional off-the-shelf NLI/LLM as explicitly labeled baselines (license and offline/privacy audited).
Measure: per-class precision/recall, critical-edit miss rate, safe-rewrite alarm rate, reviewer time, latency, memory, package/installation cost; report counts, sample sizes and uncertainty intervals. Test meaningful paired comparisons where appropriate. Record negative cases.

**Gate D:** Do not claim improvement, superiority, novelty, production safety, or statistical significance until independently evaluated and supported.

### Phase E — Useful release
Ship one documented CLI flow on real, permitted developer docs; explicit manual review requirements; reproducible install/tests; optional PR reporting if proven useful. Obtain user feedback and measure false alarms. No website unless clearly justified.

### Phase F — Research paper
Only once Phases B–D yield credible reproducible evidence: literature and competitor comparison, research questions, dataset ethics/licensing, system description, exact baselines, results, uncertainty, limitations, threats to validity, replication instructions. A PDF is a format; not evidence or acceptance by a venue. Publish negative results honestly.

## 5. Immediate decision queue (no code edits until Gate A)

1. **Independent research delegation:** ask Claude Opus to reproduce/critique reuse matrix and score candidate *fit* with actual commands and exact versions. Open a dedicated GitHub issue. It must not implement, rewrite code, or assume which architecture wins.
2. Separately reproduce known three failures as explicit baseline evidence.
3. Prepare a small evaluation fixture pack; track provenance, approvals and harmless counterexamples.
4. Review independent evidence and choose which existing OSS tool(s) to integrate; obtain Amar's approval before refactoring.

## 6. Minimum issue/PR template

**Problem and real-world affected reader** | **exact failing example** | **primary source and links** | **existing tools already evaluated** | **license/privacy result** | **smallest proposed change** | **baseline + negative counterexample** | **measurement or test** | **unsupported assumptions** | **reviewer and rollback**.

The default answer to an unproven requested feature is `RESEARCH REQUIRED`, not speculative implementation.

## Primary references

- ASD publisher: https://www.asd-ste100.org/
- Empirical documentation failures: https://www.cs.mcgill.ca/~martin/papers/ieeesw2015.pdf
- Vale: https://github.com/vale-cli/vale
- textlint: https://github.com/textlint/textlint
- ste-cli: https://github.com/TudorAndrei/ste-cli
- ste100: https://github.com/Kopachelli/ste100
- Vale STE rules: https://github.com/amoslives/vale-ste
- Alternative STE linter: https://github.com/stuffbucket/vale
- spaCy: https://github.com/explosion/spaCy
- reviewdog: https://github.com/reviewdog/reviewdog
- LanguageTool license: https://github.com/languagetool-org/languagetool
- LLM judge bias: https://arxiv.org/abs/2306.05685
- Model weights licensing caveat: https://huggingface.co/docs/hub/main/repositories-licenses
- Research reporting guidance: https://github.com/acl-org/aclrollingreview/blob/main/reviewerguidelines.md
