"""Reproduce engineering probes; intended labels are not independent human gold."""
import argparse
import difflib
import hashlib
import importlib.metadata
import json
import platform
import socket
import subprocess
import sys
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.revision_compare import compare_documents

BASELINE = "dada59452ad4b18cb43e23619650d240edcea1eb"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--radar-source", type=Path, help="Optional separately checked-out Radar repository")
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).with_name("fixtures.json"))
    parser.add_argument("--previous-block-ref", help="Optional Git revision for before/after block-adapter evidence")
    args = parser.parse_args()
    frozen = subprocess.run(["git", "show", f"{BASELINE}:scripts/ste_audit.py"], cwd=ROOT, check=True, text=True, capture_output=True).stdout
    baseline = types.ModuleType("frozen_baseline")
    exec(compile(frozen, f"{BASELINE}:scripts/ste_audit.py", "exec"), baseline.__dict__)
    fixture_path = args.fixtures
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    previous = None
    if args.previous_block_ref:
        previous_source = subprocess.run(["git", "show", f"{args.previous_block_ref}:scripts/revision_compare.py"], cwd=ROOT, check=True, text=True, capture_output=True).stdout
        previous = types.ModuleType("previous_block_adapter")
        exec(compile(previous_source, "previous_block_adapter", "exec"), previous.__dict__)
    radar, radar_pin = None, None
    if args.radar_source:
        sys.path.insert(0, str(args.radar_source.resolve()))
        from radar.compare import compare_documents as radar
        radar_pin = subprocess.run(["git", "rev-parse", "HEAD"], cwd=args.radar_source, check=True, capture_output=True, text=True).stdout.strip()

    def no_network(*_args, **_kwargs):
        raise RuntimeError("Network is disabled for fixture comparisons")

    socket.socket = no_network
    outputs = []
    for case in data["cases"]:
        original, proposed = case["original"], case["proposed"]
        before, after = original.splitlines(keepends=True), proposed.splitlines(keepends=True)
        # Execute ordinary POSIX diff independently of Python's diff implementation.
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            old, new = Path(folder) / "original.md", Path(folder) / "proposed.md"
            old.write_text(original, encoding="utf-8")
            new.write_text(proposed, encoding="utf-8")
            diff = subprocess.run(["diff", "-u", "--label", "original.md", "--label", "proposed.md", str(old), str(new)], capture_output=True, text=True)
            if diff.returncode not in {0, 1}:
                raise RuntimeError(diff.stderr)
        started = time.perf_counter()
        result = compare_documents(original, proposed, "original.md", "proposed.md")
        elapsed_ms = (time.perf_counter() - started) * 1000
        row = {
            "id": case["id"], "intent": case["intent"],
            "ordinary_diff": {"alert": diff.returncode == 1, "output": diff.stdout},
            "difflib": {"alert": bool(list(difflib.unified_diff(before, after))), "opcodes": difflib.SequenceMatcher(None, before, after, autojunk=False).get_opcodes()},
            "baseline": baseline.compare(original, proposed),
            "blocks": result, "blocks_elapsed_ms": elapsed_ms,
        }
        if radar:
            row["radar_lexical"] = radar(original, proposed, backend="lexical", profile="baseline")
        if previous:
            row["previous_blocks"] = previous.compare_documents(original, proposed, "original.md", "proposed.md")
        outputs.append(row)

    summary = {}
    for name in ["ordinary_diff", "difflib", "baseline", "blocks"] + (["radar_lexical"] if radar else []) + (["previous_blocks"] if previous else []):
        def alerted(row):
            result = row[name]
            if name in {"ordinary_diff", "difflib"}:
                return result["alert"]
            if name == "baseline":
                return bool(result["protected_token_changes"])
            if name in {"blocks", "previous_blocks"}:
                return bool(result["revision_changes"])
            return any(c["status"] != "unchanged" or c["moved"] for c in result["changes"])
        summary[name] = {"changed_intent_alerts": sum(alerted(r) for r in outputs if r["intent"] == "changed"),
                         "preserved_intent_alerts": sum(alerted(r) for r in outputs if r["intent"] == "preserved"),
                         "unalerted_changed_ids": [r["id"] for r in outputs if r["intent"] == "changed" and not alerted(r)],
                         "alerted_preserved_ids": [r["id"] for r in outputs if r["intent"] == "preserved" and alerted(r)]}
    document = {
        "scope": "Engineering fixtures only. Model-assisted intended labels; not human gold, benchmark accuracy, or evidence of usefulness.",
        "baseline_commit": BASELINE, "baseline_source_sha256": hashlib.sha256(frozen.encode()).hexdigest(),
        "fixture_sha256": hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
        "radar_commit": radar_pin, "radar_profile": "baseline" if radar else None,
        "previous_block_ref": args.previous_block_ref,
        "block_source_sha256": hashlib.sha256((ROOT / "scripts/revision_compare.py").read_bytes()).hexdigest(),
        "environment": {"python": platform.python_version(), "platform": platform.platform(),
                        "markdown-it-py": importlib.metadata.version("markdown-it-py"), "mdurl": importlib.metadata.version("mdurl"),
                        "diff": subprocess.run(["diff", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]},
        "command": sys.argv, "summary": summary, "cases": outputs,
    }
    args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
