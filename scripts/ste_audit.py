#!/usr/bin/env python3
"""Offline, read-only *partial structural* review for STE-inspired documentation.

Not an ASD-endorsed tool, full rule checker, compliance certificate, or proof of
semantic equivalence. Ships no copyrighted standard vocabulary.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

VERSION = "1.2.0"
PATTERN_CODE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
PATTERN_INLINE = re.compile(r"`[^`\n]*`")
PATTERN_URL = re.compile(r"(?:https?://|www\.)\S+", re.I)
PATTERN_MARKDOWN_LINK = re.compile(r"\[([^]]+)\]\([^)]+\)")
PATTERN_WORD = re.compile(r"\b(?:[A-Za-z]+(?:['-][A-Za-z]+)*|\d+(?:\.\d+)?)(?:[-/][A-Za-z0-9]+)*\b")
PATTERN_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\"'])")
PATTERN_PASSIVE = re.compile(r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?[A-Za-z]+(?:ed|en)\b", re.I)
PATTERN_CONDITION_LAST = re.compile(r"^\s*(?:[A-Z][^.!?]+),\s*if\s+", re.I)
PATTERN_NUMBERS = re.compile(r"(?<![\w.])\d+(?:\.\d+)?(?:\s*(?:%|°[CF]|ms|s|sec|min|h|hrs|mA|A|V|W|kW|MB|GB|KiB|MiB|GiB|mm|cm|m|km|kg|g|mg|Hz|kHz|MHz|GHz))?(?!\w)", re.I)
PATTERN_MODAL = re.compile(r"\b(may|might|must|shall|should|can|cannot|can't|could|will|would|only|except|unless|never|not|no|without|before|after|until|if|when)\b", re.I)
PATTERN_ASSIGNMENT = re.compile(r"(?:--[a-z][\w-]*|[A-Za-z_]\w*)=(?:true|false|on|off|0|1|[\w.\-]+)\b", re.I)
PATTERN_IDENTIFIERS = re.compile(r"(?:--[a-z][\w-]*|\b[A-Za-z_]\w*(?:[./][A-Za-z_]\w*)+\b|\b[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+\b)")
PATTERN_CONTRACTION = re.compile(r"\b(?:can't|cannot\'t|won't|don't|doesn't|didn't|isn't|aren't|wasn't|weren't|haven't|hasn't|hadn't|couldn't|wouldn't|shouldn't|mustn't|it's|that's|they're|we're|you're|I'm|I've|we've|they've|I'll|we'll|they'll)\b", re.I)
PATTERN_NOTE_ACTION = re.compile(r"^\s*NOTE\s*:\s*(?:install|remove|disconnect|connect|start|stop|open|close|set|turn|replace|restart|run|delete|press|tighten|loosen|adjust|make sure)\b", re.I)
PATTERN_PARENS = re.compile(r"\([^()]*\)")
PATTERN_QUOTED = re.compile(r'(?:“[^”\n]+”|"[^"\n]+")')
PATTERN_SAFETY_LABEL = re.compile(r"(?im)^\s*(?:>\s*)?(WARNING|CAUTION|NOTE)\s*:")
PATTERN_NUMBER_UNIT = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?\s*(?:mm|cm|km|kg|mg|kW|mW|GHz|MHz|kHz|Hz|MB|GB|MiB|GiB|mA|ms|sec|min|hrs|hour|hours|meter|meters|feet|ft|in|lb|rpm|V|W|A|g|m|h|s|%|°C|°F)\b", re.I)
PATTERN_MODAL_CONTEXT = re.compile(r"\b(?:may|might|must|shall|should|can|cannot|can't|could|will|would|only|except|unless|never|not|no|without|before|after|until|if|when)\b", re.I)
SKIP_PREFIXES = ("#", "<!--", "-->")


def select_prose(source: str) -> list[tuple[int, str]]:
    """Extract likely prose; exclude only unambiguous non-prose. Not a Markdown parser."""
    result = []
    fence = None
    for lineno, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        m = PATTERN_CODE_FENCE.match(line)
        if m:
            marker = m.group(1)[0]
            if fence is None:
                fence = marker
            elif fence == marker:
                fence = None
            continue
        if fence or not line or line.startswith(SKIP_PREFIXES) or line.startswith("|"):
            continue
        if re.match(r"^([-*+]\s+|\d+[.)]\s+)", line):
            line = re.sub(r"^([-*+]\s+|\d+[.)]\s+)", "", line)
        line = PATTERN_MARKDOWN_LINK.sub(r"\1", line)
        line = PATTERN_INLINE.sub("CODE", line)
        line = PATTERN_URL.sub("URL", line)
        line = re.sub(r"<[^>]+>", "", line)
        if PATTERN_WORD.search(line):
            result.append((lineno, line))
    return result


def sentences(source: str) -> list[tuple[int, str]]:
    output = []
    for lineno, line in select_prose(source):
        # A deliberately conservative splitter. Abbreviations may need review.
        for sentence in PATTERN_SENTENCE.split(line):
            if sentence.strip():
                output.append((lineno, sentence.strip()))
    return output


def approximate_ste_word_count(sentence: str) -> int:
    """Conservative screening count; not the exhaustive rule 8.4-8.7 algorithm.

    Counts simple parentheses groups, quoted text and number+unit pairs as one. It cannot
    reliably identify named entities, titles, quoted placards, nested clauses,
    or every official list/colon exception.
    """
    candidate = sentence
    for _ in range(4):
        replaced = PATTERN_PARENS.sub(" ONEWORD ", candidate)
        if replaced == candidate:
            break
        candidate = replaced
    candidate = PATTERN_NUMBER_UNIT.sub(" ONEWORD ", candidate)
    candidate = PATTERN_QUOTED.sub(" ONEWORD ", candidate)
    return len(PATTERN_WORD.findall(candidate))


def prose_paragraphs(source: str) -> list[tuple[int, str]]:
    """Best-effort paragraph grouping, excluding fenced code and tables."""
    selected = dict(select_prose(source))
    groups = []
    first = None
    buff = []
    for lineno, raw in enumerate(source.splitlines(), 1):
        if lineno not in selected:
            if buff:
                groups.append((first, " ".join(buff)))
                first, buff = None, []
            continue
        if first is None:
            first = lineno
        buff.append(selected[lineno])
    if buff:
        groups.append((first, " ".join(buff)))
    return groups


def scan(source: str, mode: str) -> dict:
    findings = []
    screened_sentences = sentences(source)
    for lineno, sentence in screened_sentences:
        is_note = bool(re.match(r"^\s*NOTE\s*:", sentence, re.I))
        threshold = 25 if mode == "description" or is_note else 20
        count = approximate_ste_word_count(sentence)
        if count > threshold:
            findings.append({"line": lineno, "check": "sentence_length_candidate", "rule_id": "6.3" if mode == "description" or is_note else "5.1", "severity": "review", "words_approx": count, "threshold": threshold, "excerpt": sentence[:240], "explanation": "Approximate STE-informed count; parentheses and number+unit pairs may count once, while other exceptions still require manual checking."})
        if PATTERN_PASSIVE.search(sentence):
            findings.append({"line": lineno, "check": "passive_voice_candidate", "rule_id": "3.6", "severity": "review", "excerpt": sentence[:240], "explanation": "Pattern only; a descriptive passive can be allowed when the agent is unknown."})
        if PATTERN_CONDITION_LAST.search(sentence):
            findings.append({"line": lineno, "check": "condition_order_candidate", "rule_id": "5.4", "severity": "review", "excerpt": sentence[:240], "explanation": "Check the prerequisite and punctuation against actual procedure context."})
        if ";" in sentence:
            findings.append({"line": lineno, "check": "semicolon_candidate", "rule_id": "8.1", "severity": "review", "excerpt": sentence[:240], "explanation": "STE prose excludes semicolons. Preserve programming syntax in code."})
        if PATTERN_CONTRACTION.search(sentence):
            findings.append({"line": lineno, "check": "contraction_candidate", "rule_id": "4.2", "severity": "review", "excerpt": sentence[:240], "explanation": "A possible contraction appears in prose. Check the grammar and meaning."})
        if mode == "procedure" and PATTERN_NOTE_ACTION.search(sentence):
            findings.append({"line": lineno, "check": "note_command_candidate", "rule_id": "5.5", "severity": "review", "excerpt": sentence[:240], "explanation": "Notes should convey information, not work instructions."})
    if mode == "description":
        for lineno, paragraph in prose_paragraphs(source):
            count = len([x for x in PATTERN_SENTENCE.split(paragraph) if x.strip()])
            if count > 6:
                findings.append({"line": lineno, "check": "paragraph_sentence_count_candidate", "rule_id": "6.6", "severity": "review", "sentences_approx": count, "threshold": 6, "excerpt": paragraph[:240], "explanation": "Paragraph has more than six apparent sentences; splitting is approximate."})
    return {
        "tool": "STE Precision local screening", "tool_version": VERSION,
        "reference_issue": "ASD-STE100 Issue 9 (2025-01-15)",
        "review_status": "PARTIAL_STRUCTURAL_REVIEW", "lexical_status": "UNVERIFIED_LEXICAL",
        "mode": mode, "prose_sentences_screened": len(screened_sentences),
        "supported_rule_candidate_ids": ["3.6", "4.2", "5.1", "5.4", "5.5", "6.3", "6.6", "8.1", "8.5", "8.6", "8.7"],
        "limitations": ["Not ASD-certified or endorsed", "Approximate sentence/word/paragraph counting (including simple quotes) and heuristic passive detection", "No licensed official dictionary, word sense, POS, inflection or technical-term approval checks", "Does not implement all 53 rules or prove text meaning or compliance", "Protected tokens can change meaning without detectable token differences"],
        "findings": findings,
    }


def protected(text: str) -> dict[str, Counter]:
    return {
        "numeric_units": Counter(x.strip().lower() for x in PATTERN_NUMBERS.findall(text)),
        "modal_polarity_condition": Counter(x.lower() for x in PATTERN_MODAL.findall(text)),
        "urls": Counter(x.rstrip(".,); ") for x in PATTERN_URL.findall(text)),
        "inline_literals": Counter(PATTERN_INLINE.findall(text)),
        "identifiers": Counter(PATTERN_IDENTIFIERS.findall(text)),
        "safety_labels": Counter(label.upper() for label in PATTERN_SAFETY_LABEL.findall(text)),
        "assignments": Counter(PATTERN_ASSIGNMENT.findall(text)),
    }


def compare(original: str, proposed: str) -> dict:
    original_tokens = protected(original)
    new_tokens = protected(proposed)
    changes = []
    for key in original_tokens:
        before, after = original_tokens[key], new_tokens[key]
        removed = list((before - after).elements())
        added = list((after - before).elements())
        if removed or added:
            changes.append({"category": key, "removed": removed, "added": added, "priority": "expert-review"})
    # Compare the immediate contexts around modal and safety terms. This detects
    # simple scope changes missed by unordered token checks; it also yields
    # false positives when wording changes safely.
    def modal_contexts(value: str) -> Counter:
        tokens = re.findall(r"[A-Za-z0-9_]+|--[a-z][\w-]*", value.lower())
        contexts = []
        for i, word in enumerate(tokens):
            if PATTERN_MODAL_CONTEXT.fullmatch(word):
                contexts.append(" ".join(tokens[max(0, i-3):i+4]))
        return Counter(contexts)
    old_scopes, new_scopes = modal_contexts(original), modal_contexts(proposed)
    if old_scopes != new_scopes:
        changes.append({"category": "modal_scope_context", "removed": list((old_scopes-new_scopes).elements()), "added": list((new_scopes-old_scopes).elements()), "priority": "expert-review", "explanation": "Windowed context differs; screen for negation, authorization, and condition scope changes. Heuristic only."})
    return {
        "review_status": "EXPERT_REVIEW_REQUIRED" if changes else "PARTIAL_STRUCTURAL_REVIEW",
        "note": "Token equality is not semantic equivalence. Differences may be benign; omissions may remain undetected.",
        "protected_token_changes": changes,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("file", type=Path, help="UTF-8 Markdown or text file; never modified")
    p.add_argument("--mode", choices=["procedure", "description"], required=True)
    p.add_argument("--compare", type=Path, help="Optional original file to screen for protected-token changes")
    p.add_argument("--compare-method", choices=["tokens", "blocks"], default="tokens", help="tokens: original heuristic; blocks: optional located Markdown text diff (not semantic judgment)")
    p.add_argument("--format", choices=["json", "text"], default="text")
    p.add_argument("--fail-on-length", action="store_true", help="Exit 2 on heuristic length candidates; does not certify STE")
    args = p.parse_args(argv)
    if args.compare_method == "blocks" and not args.compare:
        p.error("--compare-method blocks requires --compare")
    try:
        source = args.file.read_text(encoding="utf-8")
        report = scan(source, args.mode)
        if args.compare:
            original = args.compare.read_text(encoding="utf-8")
            if args.compare_method == "blocks":
                from revision_compare import compare_documents
                report["comparison"] = compare_documents(original, source, str(args.compare), str(args.file))
            else:
                report["comparison"] = compare(original, source)
    except (OSError, UnicodeError, RuntimeError, ValueError) as e:
        print(f"Cannot read input: {e}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"{report['review_status']} / {report['lexical_status']} — {len(report['findings'])} candidates")
        for finding in report["findings"]:
            print(f"L{finding['line']}: {finding['check']} — {finding['excerpt']}")
        if "comparison" in report:
            comparison = report["comparison"]
            key = "revision_changes" if args.compare_method == "blocks" else "protected_token_changes"
            print("Revision text changes:" if args.compare_method == "blocks" else "Protected-token changes:", json.dumps(comparison[key], ensure_ascii=False))
        print("Not full STE compliance. Human review and official Issue 9 required.")
    return 2 if args.fail_on_length and any(f["check"] == "sentence_length_candidate" for f in report["findings"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
