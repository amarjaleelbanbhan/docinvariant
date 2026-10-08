# Research roadmap — evidence before paper

**Working question:** Can a hybrid structural + semantic-invariant documentation auditor detect high-consequence meaning changes more reliably than a simple diff, a rule-only baseline, and an LLM-only review?

This is a research hypothesis, **not a demonstrated result**. The current project is a prototype, not an accepted paper.

## Study design (proposed)

1. Create a transparent, license-safe corpus of original paired technical instructions, including harmless rewrites, negation reversals, authorization flips, actor/object swaps, modality changes, quantity changes, and condition/scope changes.
2. Include realistic original examples from permitted documents where licensing allows. Avoid copying restricted standards or proprietary manuals.
3. Have qualified reviewers label whether meaning changed, the failure class, severity, and evidence span. Record disagreements, adjudication, and uncertainty.
4. Compare: naive token diff; existing DocInvariant CLI; proposed parser-based invariant detector; and a documented LLM-only baseline with controlled prompt, model/version, and sampling settings.
5. Measure precision, recall, **critical-change false-negative rate**, false-positive rate on safe rewrites, latency, and operational reviewer load. Report sample sizes and uncertainty intervals. Pre-register the analysis before final evaluation.
6. Split by template/source/project to avoid near-duplicate leakage between training and test. Keep an untouched holdout set.
7. Publish code, test fixtures and labels when legally permissible; disclose any restricted datasets and all reproducibility limits.

## Publication standard

Do not claim novelty or superiority without comparing prior systems and conducting experiments. Describe the ASD-STE100 Issue 9 standard accurately but neither claim official certification nor reproduce its dictionary. Separate writing-rule audits from semantic change detection. Report negative results and known failures.

Potential output: technical report/preprint followed by a suitable peer-reviewed software-engineering/NLP venue. No experimental results are claimed here.
