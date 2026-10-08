"""Located textual revision screening; no semantic or technical judgment."""
from __future__ import annotations

import re
from difflib import SequenceMatcher
from importlib.metadata import version

MAX_CHARACTERS = 200_000
MAX_BLOCKS = 2_000
CONTAINERS = {"blockquote_open", "bullet_list_open", "ordered_list_open", "list_item_open"}


def _inline_key(children: list) -> tuple:
    """Ignore prose wrapping/emphasis, retain code and destination identity."""
    parts, text = [], []

    def flush():
        if text:
            parts.append(("text", re.sub(r"\s+", " ", "".join(text))))
            text.clear()

    for token in children:
        if token.type == "text":
            text.append(token.content)
        elif token.type in {"softbreak", "hardbreak"}:
            text.append(" ")
        elif token.type in {"em_open", "em_close", "strong_open", "strong_close"}:
            continue
        else:
            flush()
            parts.append((token.type, token.content, tuple(sorted(token.attrs.items()))))
    flush()
    return tuple(parts)


def _blocks(source: str, parser, path: str) -> list[dict]:
    lines = source.splitlines(keepends=True)
    tokens = parser.parse(source)
    blocks, stack, covered = [], [], set()

    def add(token, key, source_map=None):
        start, end = source_map if source_map is not None else token.map
        covered.update(range(start, end))
        blocks.append({"key": key, "span": {
            "path": path, "line_start": start + 1, "line_end": end,
            "text": "".join(lines[start:end]), "kind": token.type,
        }})

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type in CONTAINERS:
            start = (token.attrGet("start") or 1) if token.type == "ordered_list_open" else None
            stack.append((token.type, start))
        elif token.nesting == -1 and token.type.replace("_close", "_open") in CONTAINERS:
            stack.pop()
        elif token.type == "table_open":
            cells = []
            cursor = index + 1
            while tokens[cursor].type != "table_close":
                item = tokens[cursor]
                cells.append((item.type, _inline_key(item.children or []) if item.type == "inline" else ()))
                cursor += 1
            add(token, (tuple(stack), "table", tuple(cells)))
            index = cursor
        elif token.type == "inline" and token.map:
            parent = tokens[index - 1]
            source_map = parent.map if parent.type == "heading_open" else token.map
            add(token, (tuple(stack), parent.tag, _inline_key(token.children or [])), source_map)
        elif token.type in {"fence", "code_block", "html_block", "hr"} and token.map:
            kind = "code" if token.type in {"fence", "code_block"} else token.type
            add(token, (tuple(stack), kind, token.info, token.content))
        index += 1

    # Keep syntax omitted from the AST without inventing another parser.
    for index, line in enumerate(lines):
        if index not in covered and line.strip():
            blocks.append({"key": ("unmapped_source", line.rstrip("\r\n")), "span": {
                "path": path, "line_start": index + 1, "line_end": index + 1,
                "text": line, "kind": "unmapped_source",
            }})
    blocks.sort(key=lambda block: block["span"]["line_start"])
    if len(blocks) > MAX_BLOCKS:
        raise ValueError(f"Block comparison supports at most {MAX_BLOCKS} blocks per input; split the document.")
    return blocks


def compare_documents(original: str, proposed: str, original_path: str = "<original>", proposed_path: str = "<proposed>") -> dict:
    """Diff ordered Markdown blocks, retaining exact raw source line ranges.

    Replacement groups are not claimed to be aligned sentences or equivalent
    propositions. Additions, deletions and moves require human review.
    """
    if max(len(original), len(proposed)) > MAX_CHARACTERS:
        raise ValueError(f"Block comparison supports at most {MAX_CHARACTERS} characters per input; split the document.")
    try:
        from markdown_it import MarkdownIt
    except ImportError as error:
        raise RuntimeError("Block comparison requires: python -m pip install -r requirements-comparison.txt") from error
    parser = MarkdownIt("commonmark").enable("table")
    before = _blocks(original, parser, original_path)
    after = _blocks(proposed, parser, proposed_path)
    matcher = SequenceMatcher(None, [b["key"] for b in before], [b["key"] for b in after], autojunk=False)
    changes = [{
        "operation": operation, "original": [b["span"] for b in before[i:j]],
        "proposed": [b["span"] for b in after[k:l]],
        "priority": "human-review", "explanation": "Text or document structure differs; review intent and correctness.",
    } for operation, i, j, k, l in matcher.get_opcodes() if operation != "equal"]
    return {
        "method": "markdown-block-diff", "schema_version": 1,
        "parser": {"name": "markdown-it-py", "version": version("markdown-it-py"), "preset": "commonmark+table"},
        "review_status": "TEXT_CHANGES_REQUIRE_REVIEW" if changes else "NO_REPORTED_TEXT_CHANGE",
        "semantic_status": "NOT_ASSESSED", "original_blocks": len(before), "proposed_blocks": len(after),
        "coverage_notes": [
            "Textual screening only; no findings does not prove semantic equivalence or safety.",
            "Prose whitespace, soft/hard wrapping, emphasis and bullet marker style are normalized; code whitespace is retained.",
            "HTML and unmapped source are compared as raw text; embedded languages and Markdown extensions are not interpreted.",
            "Moves and sentence splits/merges may appear as insertion/deletion or replacement groups; role and quantity ownership are not inferred.",
        ],
        "revision_changes": changes,
    }
