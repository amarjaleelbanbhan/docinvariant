import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ste_audit.py"
spec = importlib.util.spec_from_file_location("ste_audit", SCRIPT)
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class StructuralChecks(unittest.TestCase):
    def test_short_instruction(self):
        self.assertEqual(audit.scan("Install the module.", "procedure")["findings"], [])

    def test_21_words_procedure_flag(self):
        sentence = " ".join("word" for _ in range(21)) + "."
        self.assertEqual(audit.scan(sentence, "procedure")["findings"][0]["check"], "sentence_length_candidate")

    def test_20_words_procedure_allowed(self):
        sentence = " ".join("word" for _ in range(20)) + "."
        self.assertEqual(audit.scan(sentence, "procedure")["findings"], [])

    def test_26_words_description_flag(self):
        sentence = " ".join("word" for _ in range(26)) + "."
        self.assertEqual(audit.scan(sentence, "description")["findings"][0]["check"], "sentence_length_candidate")

    def test_25_words_description_allowed(self):
        sentence = " ".join("word" for _ in range(25)) + "."
        self.assertEqual(audit.scan(sentence, "description")["findings"], [])

    def test_fenced_code_skipped(self):
        self.assertEqual(audit.scan("```python\n" + " ".join("test" for _ in range(45)) + "\n```", "procedure")["findings"], [])

    def test_tilde_fenced_code_skipped(self):
        self.assertEqual(audit.scan("~~~\n" + " ".join("test" for _ in range(45)) + "\n~~~", "procedure")["findings"], [])

    def test_inline_code_is_one_marker(self):
        s = "Use `" + " ".join("parameter" for _ in range(80)) + "` now."
        self.assertEqual(audit.scan(s, "procedure")["findings"], [])

    def test_heading_and_table_skipped(self):
        s = "# Heading containing lots of words " + " long" * 30 + "\n| column | column |\n|----|----|"
        self.assertEqual(audit.scan(s, "procedure")["findings"], [])

    def test_bullet_detected(self):
        s = "- " + " ".join("word" for _ in range(21)) + "."
        self.assertEqual(audit.scan(s, "procedure")["findings"][0]["check"], "sentence_length_candidate")

    def test_passive_candidate(self):
        self.assertTrue(any(f["check"] == "passive_voice_candidate" for f in audit.scan("The cable was disconnected.", "procedure")["findings"]))

    def test_imperative_no_passive(self):
        self.assertEqual(audit.scan("Disconnect the cable.", "procedure")["findings"], [])

    def test_conditional_at_start(self):
        self.assertEqual(audit.scan("If the power is off, remove the cover.", "procedure")["findings"], [])

    def test_never_claims_compliance(self):
        output = audit.scan("Remove the cover.", "procedure")
        self.assertEqual(output["lexical_status"], "UNVERIFIED_LEXICAL")
        self.assertNotIn("compliant", output["review_status"].lower())

    def test_number_decimal_counted_once(self):
        self.assertEqual(len(audit.PATTERN_WORD.findall("Set value to 3.14.")), 4)

    def test_readonly_source_not_mutated(self):
        source = "Do not change the original source."
        self.assertEqual(audit.scan(source, "description")["findings"], [])
        self.assertEqual(source, "Do not change the original source.")


class MeaningRiskScreen(unittest.TestCase):
    def test_negation_removed(self):
        changes = audit.compare("Do not restart the server.", "Restart the server.")
        self.assertEqual(changes["review_status"], "EXPERT_REVIEW_REQUIRED")
        self.assertTrue(any(x["category"] == "modal_polarity_condition" for x in changes["protected_token_changes"]))

    def test_modal_change(self):
        changes = audit.compare("The machine may stop.", "The machine must stop.")
        self.assertEqual(changes["review_status"], "EXPERT_REVIEW_REQUIRED")

    def test_numeric_difference(self):
        changes = audit.compare("Wait 15 min.", "Wait 5 min.")
        self.assertTrue(any(x["category"] == "numeric_units" for x in changes["protected_token_changes"]))

    def test_identifier_change(self):
        changes = audit.compare("Use --force=false.", "Use --force=true.")
        self.assertEqual(changes["review_status"], "EXPERT_REVIEW_REQUIRED")

    def test_url_change(self):
        changes = audit.compare("Use https://a.example/docs", "Use https://b.example/docs")
        self.assertTrue(any(x["category"] == "urls" for x in changes["protected_token_changes"]))

    def test_equal_tokens_are_not_equivalence(self):
        changes = audit.compare("Allow Anna, not Bob.", "Allow Bob, not Anna.")
        self.assertIn("not semantic equivalence", changes["note"])

    def test_inline_code_protected(self):
        changes = audit.compare("Run `npm install`.", "Run `npm update`.")
        self.assertTrue(any(x["category"] == "inline_literals" for x in changes["protected_token_changes"]))

    def test_compare_numbers_with_units(self):
        changes = audit.compare("Keep below 5 V.", "Keep below 5 A.")
        self.assertTrue(any(x["category"] == "numeric_units" for x in changes["protected_token_changes"]))


class IssueNineRegressions(unittest.TestCase):
    def checks(self, value, mode="procedure"):
        return [f["check"] for f in audit.scan(value, mode)["findings"]]

    def test_number_unit_counts_one(self):
        self.assertEqual(audit.approximate_ste_word_count("Wait for 25 min."), 3)

    def test_parentheses_count_one(self):
        self.assertEqual(audit.approximate_ste_word_count("Use the part (with a very long official serial number)."), 4)

    def test_semicolon_in_prose_flagged(self):
        self.assertIn("semicolon_candidate", self.checks("Install the valve; restart the system."))

    def test_semicolon_in_code_fence_is_ignored(self):
        self.assertEqual(self.checks("```javascript\nlet a = 1; let b = 2;\n```"), [])

    def test_contraction_candidate(self):
        self.assertIn("contraction_candidate", self.checks("Don't disconnect the cable."))

    def test_no_false_contraction_on_possessive(self):
        self.assertNotIn("contraction_candidate", self.checks("The user's cable is ready."))

    def test_description_seven_sentences_flagged(self):
        sample=" ".join("This works." for _ in range(7))
        self.assertIn("paragraph_sentence_count_candidate", self.checks(sample,"description"))

    def test_description_six_sentences_not_flagged(self):
        sample=" ".join("This works." for _ in range(6))
        self.assertNotIn("paragraph_sentence_count_candidate", self.checks(sample,"description"))

    def test_procedure_notes_25_words(self):
        text="NOTE: " + " ".join("word" for _ in range(24)) + "."
        self.assertNotIn("sentence_length_candidate",self.checks(text))

    def test_procedure_notes_26_words(self):
        text="NOTE: " + " ".join("word" for _ in range(25)) + "."
        self.assertIn("sentence_length_candidate",self.checks(text))

    def test_note_with_command_flagged(self):
        self.assertIn("note_command_candidate",self.checks("NOTE: Remove the access panel."))

    def test_note_with_information_not_flagged(self):
        self.assertNotIn("note_command_candidate",self.checks("NOTE: The panel is optional."))

    def test_number_and_unit_keep_sentence_within_limit(self):
        sample=" ".join("word" for _ in range(18)) + " 15 mm."
        self.assertNotIn("sentence_length_candidate",self.checks(sample))

    def test_modal_scope_change_even_with_same_tokens(self):
        result=audit.compare("Allow Anna, not Bob.", "Allow Bob, not Anna.")
        self.assertTrue(any(f["category"]=="modal_scope_context" for f in result["protected_token_changes"]))

    def test_reordered_constraint_scopes(self):
        result=audit.compare("Back up files before deleting them.", "Delete files before backing them up.")
        self.assertEqual(result["review_status"],"EXPERT_REVIEW_REQUIRED")

    def test_rule_ids_present(self):
        finding=audit.scan("Use this; but not that.","procedure")["findings"]
        self.assertEqual(finding[0]["rule_id"],"8.1")


class CliTests(unittest.TestCase):
    def test_json_output(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "text.md"
            src.write_text("Install the module.\n", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(src), "--mode", "procedure", "--format", "json"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["review_status"], "PARTIAL_STRUCTURAL_REVIEW")

    def test_length_exit_code(self):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "text.md"
            src.write_text(" ".join("word" for _ in range(21)) + ".", encoding="utf-8")
            run = subprocess.run([sys.executable, str(SCRIPT), str(src), "--mode", "procedure", "--fail-on-length"], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)

    def test_input_missing_fails(self):
        run = subprocess.run([sys.executable, str(SCRIPT), "/nonexistent/file.md", "--mode", "description"], capture_output=True, text=True)
        self.assertEqual(run.returncode, 1)




class OfficialPdfRegressions(unittest.TestCase):
    """Targeted Issue 9 cases from official primary text, not certification tests."""
    def test_explicit_quoted_text_counts_as_one_under_rule_8_6(self):
        self.assertEqual(audit.approximate_ste_word_count('Select the “Service Overview” option.'), 4)

    def test_ascii_quoted_text_counts_as_one_under_rule_8_6(self):
        self.assertEqual(audit.approximate_ste_word_count('Select the "Service Overview" option.'), 4)

    def test_safety_label_swap_is_flagged(self):
        result = audit.compare('WARNING: Keep clear of the blade.', 'CAUTION: Keep clear of the blade.')
        self.assertEqual(result['review_status'], 'EXPERT_REVIEW_REQUIRED')
        self.assertTrue(any(x['category'] == 'safety_labels' for x in result['protected_token_changes']))

    def test_safety_label_removal_is_flagged(self):
        result = audit.compare('WARNING: Keep clear of the blade.', 'Keep clear of the blade.')
        self.assertTrue(any(x['category'] == 'safety_labels' for x in result['protected_token_changes']))

    def test_label_preservation_no_false_positive(self):
        result = audit.compare('CAUTION: Do not remove the panel.', 'CAUTION: Do not remove this panel.')
        self.assertFalse(any(x['category'] == 'safety_labels' for x in result['protected_token_changes']))

    def test_dictionary_absent_from_distributed_package(self):
        self.assertNotIn('dictionary entries', audit.scan('Install the unit.', 'procedure').get('supported_rule_candidate_ids', []))

if __name__ == "__main__":
    unittest.main()
