# Known limitations — keep visible in every evaluation

**Current checker: v1.2.0 (ported from the Amar Jarvis STE Precision v0.4.0 prototype).**

The following adversarial cases are known blind spots or weak spots. Do not call them fixed without adding regression tests and confirming behavior:

1. `NOTE: You must delete the backup file.` may not be flagged even though it contains a work instruction. The simpler `NOTE: Delete the backup file.` is recognized.
2. `Allow user access.` -> `Deny user access.` can evade comparison because the change is outside the limited list of protected tokens.
3. `The server sends data to the database.` -> `The database sends data to the server.` can evade comparison because actor/object roles are not parsed.
4. Safe paraphrases can trigger review (false positives), including logically equivalent negation variants.
5. The word-count approach is approximate; not every ASD-STE100 Issue 9 exception can be implemented with simple regular expressions.
6. A clean scan does not establish permission safety, scientific correctness, grammar correctness, semantic equivalence, or standards compliance.

These are qualitative regression observations, not a population-level accuracy score. Preserve them as negative test cases for an independently assessed next release.

## Near-term issue backlog

- Parse NOTE obligation patterns such as `you must` and validate line-level labels.
- Compare role/action/object relations and polarity in changed sentences.
- Add security permission verbs (allow, deny, grant, revoke) with explicit scope checks.
- Add a balanced corpus of safe and harmful paraphrases to measure false positives and missed meaning changes.
- Evaluate mixed procedure/description sections rather than forcing one global mode.
