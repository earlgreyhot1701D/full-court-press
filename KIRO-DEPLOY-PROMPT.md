Kiro: deploy session for Full Court Press. Read first, before anything else:
1. `git log --oneline -15` and BUILD-LOG.md from the entry "3.2 . voice_client" to the end.
2. DEPLOY.md. It is the whole job. Follow it step by step.

What changed since you last worked here: Claude built every non-AWS piece on disk (voices, fact lock,
voice client, share card, site builder, hunter, audio, template.yaml, bundle builder). 166 tests pass.
You do not write application code this session.

Your job: steps 0, 1, 2, 4, 5 and 6 of DEPLOY.md (step 0 changes a billing setting: propose first). Step 3 (sam deploy) only after the owner says go.

Guardrails:
- Propose before each AWS-changing command; wait for the owner's go.
- Do NOT run `sam build`. Use `python tools/build_lambda.py`.
- Fix only what `sam validate --lint` flags in template.yaml. DO NOT refactor other code.
- No IAM users, no access keys. Never read or print the BALLDONTLIE key. Redact the account id.
- If the first run fails, report the error type and the failing step. Do not guess a fix across files.
- Log your work in BUILD-LOG.md as "(Kiro)" entries, and findings in LEDGER.md.
