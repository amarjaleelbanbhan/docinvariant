import json
import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.revision_compare import compare_documents

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ste_audit.py"


HAS_PARSER = importlib.util.find_spec("markdown_it") is not None


@unittest.skipUnless(HAS_PARSER, "optional comparison dependencies are not installed")
class RevisionComparisonTests(unittest.TestCase):
    def test_consequential_edits_have_raw_locations(self):
        fixtures = json.loads((ROOT / "experiments/located_compare/fixtures.json").read_text())
        for case in fixtures["cases"]:
            if case["intent"] != "changed":
                continue
            with self.subTest(case=case["id"]):
                result = compare_documents(case["original"], case["proposed"], "old.md", "new.md")
                self.assertTrue(result["revision_changes"])
                for change in result["revision_changes"]:
                    for side, source in [("original", case["original"]), ("proposed", case["proposed"])]:
                        for span in change[side]:
                            self.assertEqual(span["path"], "old.md" if side == "original" else "new.md")
                            lines = source.splitlines(keepends=True)
                            self.assertEqual(span["text"], "".join(lines[span["line_start"] - 1:span["line_end"]]))

    def test_formatting_controls(self):
        fixtures = json.loads((ROOT / "experiments/located_compare/fixtures.json").read_text())
        ignored = {"unchanged", "soft_wrap", "emphasis", "fence_marker", "bullet_marker", "blank_lines"}
        for case in fixtures["cases"]:
            if case["id"] in ignored:
                with self.subTest(case=case["id"]):
                    self.assertEqual(compare_documents(case["original"], case["proposed"])["revision_changes"], [])

    def test_paraphrase_is_reviewed_not_declared_changed_meaning(self):
        result = compare_documents("Do not share the phrase.", "Never share the phrase.")
        self.assertTrue(result["revision_changes"])
        self.assertEqual(result["semantic_status"], "NOT_ASSESSED")

    def test_empty_documents_are_valid(self):
        self.assertEqual(compare_documents("", "")["revision_changes"], [])
        self.assertEqual(compare_documents("Verify the backup.", "")["revision_changes"][0]["operation"], "delete")

    def test_code_whitespace_preserved(self):
        self.assertTrue(compare_documents("`echo a  b`", "`echo a b`")["revision_changes"])
        self.assertTrue(compare_documents("```py\n  f()\n```", "```py\nf()\n```")["revision_changes"])

    def test_four_backtick_fence_not_split_at_three(self):
        result = compare_documents("````md\n```\nold\n````", "````md\n```\nnew\n````")
        self.assertEqual(len(result["revision_changes"]), 1)
        self.assertEqual(result["revision_changes"][0]["original"][0]["line_end"], 4)

    def test_reference_target_preserved(self):
        self.assertTrue(compare_documents("Read [guide][g].\n\n[g]: https://a.example", "Read [guide][g].\n\n[g]: https://b.example")["revision_changes"])

    def test_unused_reference_is_reviewable(self):
        self.assertTrue(compare_documents("[g]: https://a.example", "[g]: https://b.example")["revision_changes"])

    def test_html_preserved_with_explicit_limit(self):
        result = compare_documents("<div>Allow access</div>", "<div>Deny access</div>")
        self.assertTrue(result["revision_changes"])
        self.assertTrue(result["coverage_notes"])

    def test_duplicate_deletion_is_not_lost(self):
        result = compare_documents("Verify the backup.\n\nVerify the backup.", "Verify the backup.")
        self.assertEqual(result["revision_changes"][0]["operation"], "delete")
        self.assertEqual(result["revision_changes"][0]["original"][0]["line_start"], 3)

    def test_authored_ordered_marker_change_is_located(self):
        original = "1. Restart service.\n2. Delete backup.\n"
        proposed = "1. Restart service.\n9. Delete backup.\n"
        from markdown_it import MarkdownIt
        self.assertEqual(MarkdownIt("commonmark").render(original), MarkdownIt("commonmark").render(proposed))
        result = compare_documents(original, proposed, "old.md", "new.md")
        self.assertEqual(result["review_status"], "TEXT_CHANGES_REQUIRE_REVIEW")
        change = result["revision_changes"][0]
        self.assertEqual(change["original"][0]["line_start"], 2)
        self.assertEqual(change["proposed"][0]["line_start"], 2)
        self.assertEqual(change["original"][0]["text"], "2. Delete backup.\n")
        self.assertEqual(change["proposed"][0]["text"], "9. Delete backup.\n")

    def test_ordered_delimiter_and_spacing_are_formatting(self):
        original = "1. Restart service.\n2. Delete backup.\n"
        proposed = "1)  Restart service.\n2)  Delete backup.\n"
        self.assertEqual(compare_documents(original, proposed)["revision_changes"], [])

    def test_render_equivalent_renumbering_still_requires_authored_number_review(self):
        original = "1. Restart service.\n1. Delete backup.\n"
        proposed = "1. Restart service.\n2. Delete backup.\n"
        from markdown_it import MarkdownIt
        self.assertEqual(MarkdownIt("commonmark").render(original), MarkdownIt("commonmark").render(proposed))
        self.assertTrue(compare_documents(original, proposed)["revision_changes"])

    def test_ordered_list_start_changes_rendering(self):
        original, proposed = "2. Restart service.\n3. Delete backup.\n", "3. Restart service.\n4. Delete backup.\n"
        from markdown_it import MarkdownIt
        self.assertNotEqual(MarkdownIt("commonmark").render(original), MarkdownIt("commonmark").render(proposed))
        self.assertTrue(compare_documents(original, proposed)["revision_changes"])

    def test_nested_ordered_number_uses_parser_info(self):
        original = "> 1. Prepare.\n>    1. Restart service.\n>    2. Delete backup.\n"
        proposed = "> 1. Prepare.\n>    1. Restart service.\n>    9. Delete backup.\n"
        result = compare_documents(original, proposed)
        self.assertTrue(result["revision_changes"])
        self.assertEqual(result["revision_changes"][0]["original"][0]["line_start"], 3)

    def test_duplicate_deletion_discloses_uncertain_occurrence(self):
        original = "Verify the backup.\n\nVerify the backup.\n\nDelete the old backup.\n"
        proposed = "Verify the backup.\n\nDelete the old backup.\n"
        result = compare_documents(original, proposed)
        self.assertTrue(result["alignment_ambiguous"])
        change = result["revision_changes"][0]
        self.assertTrue(change["alignment_ambiguous"])
        self.assertIn(change["original"][0]["line_start"], {1, 3})
        self.assertEqual(change["original"][0]["text"], "Verify the backup.\n")
        self.assertTrue(any("duplicate" in note.lower() for note in result["coverage_notes"]))

    def test_duplicate_insertion_and_normalized_keys_disclose_ambiguity(self):
        result = compare_documents("Verify the backup.", "Verify the backup.\n\nVerify **the backup**.")
        self.assertTrue(result["alignment_ambiguous"])
        self.assertTrue(result["revision_changes"][0]["alignment_ambiguous"])

    def test_unchanged_duplicates_and_unique_deletion_controls(self):
        same = "Verify the backup.\n\nVerify the backup."
        self.assertEqual(compare_documents(same, same)["revision_changes"], [])
        self.assertFalse(compare_documents(same, same)["alignment_ambiguous"])
        result = compare_documents("Verify the backup.\n\nDelete the old backup.", "Verify the backup.")
        self.assertFalse(result["alignment_ambiguous"])
        self.assertFalse(result["revision_changes"][0]["alignment_ambiguous"])

    def test_warning_presentation_normalization_does_not_approve_safety(self):
        original, proposed = "**WARNING:** Keep clear.\nDo not touch the blade.", "WARNING: Keep clear.  \nDo not touch the blade."
        result = compare_documents(original, proposed)
        self.assertEqual(result["revision_changes"], [])
        self.assertEqual(result["semantic_status"], "NOT_ASSESSED")
        self.assertTrue(any("WARNING" in note for note in result["coverage_notes"]))

    def test_unicode_separators_do_not_shift_markdown_source_lines(self):
        # Python str.splitlines() recognizes these as newlines, but CommonMark
        # source maps count only CR/LF. Their offsets must not be mixed.
        for separator in ("\\u2028", "\\u2029", "\\u0085", "\\v", "\\f", "\\x1c", "\\x1d", "\\x1e"):
            separator = separator.encode("ascii").decode("unicode_escape")
            for eol in ("\\n", "\\r\\n", "\\r"):
                eol = eol.encode("ascii").decode("unicode_escape")
                with self.subTest(separator=repr(separator), eol=repr(eol)):
                    old = "Prefix" + separator + "suffix" + eol + eol + "Allow access." + eol
                    new = "Prefix" + separator + "suffix" + eol + eol + "Deny access." + eol
                    result = compare_documents(old, new, "old.md", "new.md")
                    self.assertEqual(len(result["revision_changes"]), 1)
                    change = result["revision_changes"][0]
                    self.assertEqual(change["original"][0]["line_start"], 3)
                    self.assertEqual(change["proposed"][0]["line_start"], 3)
                    self.assertEqual(change["original"][0]["text"], "Allow access." + eol)
                    self.assertEqual(change["proposed"][0]["text"], "Deny access." + eol)

    def test_container_change_is_reviewable(self):
        self.assertTrue(compare_documents("> Only if ready:\n>\n> Restart.", "Only if ready:\n\nRestart.")["revision_changes"])

    def test_unicode_and_table_ranges(self):
        result = compare_documents("# Café\n\n| User | Access |\n| --- | --- |\n| α | allow |", "# Café\n\n| User | Access |\n| --- | --- |\n| α | deny |")
        self.assertEqual(result["revision_changes"][0]["original"][0]["line_start"], 3)
        self.assertEqual(result["revision_changes"][0]["original"][0]["line_end"], 5)

    def test_too_many_blocks_fails_explicitly(self):
        with self.assertRaises(ValueError):
            compare_documents("x\n\n" * 2001, "x")

    def test_setext_heading_uses_full_source_map(self):
        self.assertEqual(compare_documents("# Setup\n", "Setup\n=====\n")["revision_changes"], [])
        change = compare_documents("Setup\n=====\n", "Setup\n-----\n")["revision_changes"][0]
        self.assertEqual(change["original"][0]["line_end"], 2)

    def test_unmapped_terminal_newline_is_not_an_edit(self):
        self.assertEqual(compare_documents("[g]: https://a.example", "[g]: https://a.example\n")["revision_changes"], [])

    def test_table_padding_and_code_emphasis_are_formatting(self):
        self.assertEqual(compare_documents("|a|b|\n|-|-|\n|x|y|", "| a | b |\n| --- | --- |\n| x | y |")["revision_changes"], [])
        self.assertEqual(compare_documents("Run `echo x`.", "Run **`echo x`**.")["revision_changes"], [])

    def test_title_and_image_destination_edits_are_preserved(self):
        self.assertTrue(compare_documents('[guide](https://a.example "allow")', '[guide](https://a.example "deny")')["revision_changes"])
        self.assertTrue(compare_documents("![diagram](old.svg)", "![diagram](new.svg)")["revision_changes"])


class RevisionCliTests(unittest.TestCase):
    @unittest.skipUnless(HAS_PARSER, "optional comparison dependencies are not installed")
    def test_cli_is_read_only_and_locates_both_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            old, new = Path(folder) / "old.md", Path(folder) / "new.md"
            old.write_text("Allow access.")
            new.write_text("Deny access.")
            run = subprocess.run([sys.executable, str(SCRIPT), str(new), "--mode", "procedure", "--compare", str(old), "--compare-method", "blocks", "--format", "json"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            result = json.loads(run.stdout)["comparison"]
            self.assertEqual(result["method"], "markdown-block-diff")
            self.assertEqual(result["revision_changes"][0]["original"][0]["path"], str(old))
            self.assertEqual(old.read_text(), "Allow access.")
            self.assertEqual(new.read_text(), "Deny access.")

    @unittest.skipUnless(HAS_PARSER, "optional comparison dependencies are not installed")
    def test_text_output_and_limit_error(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "doc.md"
            source.write_text("Install the module.")
            command = [sys.executable, str(SCRIPT), str(source), "--mode", "procedure", "--compare", str(source), "--compare-method", "blocks"]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("Revision text changes:", run.stdout)
            source.write_text("x" * 200001)
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 1)
            self.assertIn("200000 characters", run.stderr)
            self.assertIn("Comparison failed:", run.stderr)
            self.assertNotIn("Traceback", run.stderr)

    def test_bad_input_still_uses_read_error_prefix(self):
        missing = Path(tempfile.gettempdir()) / "docinvariant-unlikely-nonexistent-input-709431.md"
        self.assertFalse(missing.exists())
        run = subprocess.run(
            [sys.executable, str(SCRIPT), str(missing), "--mode", "procedure"],
            capture_output=True, text=True,
        )
        self.assertEqual(run.returncode, 1)
        self.assertIn("Cannot read input:", run.stderr)
        self.assertNotIn("Comparison failed:", run.stderr)

    def test_blocks_requires_second_input(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "unused.md", "--mode", "procedure", "--compare-method", "blocks"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 2)
        self.assertIn("requires --compare", run.stderr)

    def test_missing_dependency_is_actionable(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "doc.md"
            source.write_text("Install the module.")
            run = subprocess.run([sys.executable, "-S", str(SCRIPT), str(source), "--mode", "procedure", "--compare", str(source), "--compare-method", "blocks"], capture_output=True, text=True, env={"PATH": str(Path(sys.executable).parent)})
            self.assertEqual(run.returncode, 1)
            self.assertIn("requirements-comparison.txt", run.stderr)
            self.assertIn("Comparison failed:", run.stderr)
            self.assertNotIn("Traceback", run.stderr)


if __name__ == "__main__":
    unittest.main()
