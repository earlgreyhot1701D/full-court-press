# Kiro kickoff prompt (paste into a new Kiro chat with the full-court-press folder open)

```
We're building Full Court Press, spec-driven.

Before anything else, confirm the AWS connection is live. Run `aws sts get-caller-identity --profile fcp` and show me the result with the account id masked. If that fails, stop and tell me what it said. Do not try to create IAM users, access keys, or any other credentials.

The Agent Toolkit for AWS is installed and may have added its own AWS rules files under .kiro/steering/. Those are additions. If any of them conflict with guardrails.md, guardrails.md wins, and you stop and report the conflict instead of choosing.

Then read these, in this order:

1. .kiro/steering/guardrails.md
2. .kiro/steering/product.md
3. .kiro/steering/tech.md
4. .kiro/steering/structure.md
5. .kiro/specs/full-court-press/requirements.md
6. .kiro/specs/full-court-press/design.md
7. .kiro/specs/full-court-press/tasks.md

PRD.md is the source of truth for scope. The steering and spec files are what you follow. If any of them disagree with each other or with reality, stop and report. Do not work around it.

Treat the three spec files as the spec for this feature. Do not regenerate or rewrite them. If you think one needs a change, propose the change and wait.

Your first job is NOT to build. Reply with:
- the result of the caller-identity check
- a 5-line summary of what we're building and what we're never building
- anything in the spec that is unclear, contradicts itself, or you think is unverifiable
- your plan for Block 0 only, task by task

Then stop and wait for my approval.

Tier: Spike for all of Block 0. No tests, no pinning, no sync scripts, no README, no abstractions, nothing outside spike/ (except LEDGER.md and the repo setup in 0.1). Answer each question, record it in LEDGER.md, stop.
Definition of done for Block 0: CHECKPOINT 0 in tasks.md.
DO NOT refactor other code. DO NOT add dependencies.
If the spec and reality disagree, stop and report.
Risk level: low. Propose first. Wait for approval before implementing.
```

## Footer for every later prompt
```
Tier: <Spike|Working|Full>. <that tier's prohibitions from guardrails.md, one line>.
Definition of done: <the CHECKPOINT for this block>.
DO NOT refactor other code. DO NOT add dependencies unless this block names them.
If the spec and reality disagree, stop and report. Do not work around it.
Risk level: <low|medium|high>. Propose first. Wait for approval before implementing.
```

## If Kiro doesn't pick up hand-written spec files
Open the Specs panel. If `full-court-press` isn't listed, say: "Create a spec named full-court-press using the existing requirements.md, design.md and tasks.md in .kiro/specs/full-court-press/ as-is. Do not rewrite them." Then continue with the prompt above.
