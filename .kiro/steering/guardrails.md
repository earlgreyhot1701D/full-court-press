# Guardrails (always on)

These override anything a task seems to imply. If a task cannot be done without breaking one, STOP and report instead of working around it. If the spec and reality disagree, stop and report. Do not adapt silently.

## Feature labels
- MUST: build it fully in this spec.
- STUB: do not build. Add `# STUB(full-court-press): <what>, <how to implement later>` where it would live. No half-features.
- NEVER: the behavior must not exist.

## Rigor tiers (prohibitions, not effort levels)
Every task names its tier. The tier in the task beats any habit.
| Tier | Must NOT appear in the diff | Done when |
|---|---|---|
| Spike | test files, dependency pinning, sync or drift scripts, README, abstractions, retry policies, custom exception classes, files outside `spike/` | the yes/no question is answered. Either answer ends it. Three failed attempts is also an answer. |
| Working | tests beyond happy path + known edge cases, performance work, abstraction for a second use case that does not exist | the task's PASS line is met and the reality check passes |
| Full | nothing forbidden | 11-point checklist items for that block are done |

Good enough is the PASS line. The first result that meets it wins. Do not polish past it.

## Floor (applies from the first run, every tier)
- try/except on every network call. Failure is logged and handled, never a crash that loses the run.
- Outbound rate limit, tier request-per-minute limit and per-run request cap on BALLDONTLIE (tech.md).
- Per-run cap on Bedrock calls. Lambda timeout set.
- Logs never contain prompts, model output text, raw feed bodies, the BALLDONTLIE API key, secrets or AWS account ids.
- The API key lives in SSM Parameter Store only. Never commit it, never echo it, never put it in a task summary or a screenshot.
- Untrusted text never reaches a model: the model sees only the facts sheet our code built.

## Content NEVERs
- No real media personalities' names, voices or catchphrases, in prompts or output.
- No logos, player photos or league marks. Text and original graphics only.
- Nothing about players' bodies, personal lives, off-court matters or injuries.
- Losing-side editions: honest about the loss, credit the opponent, never mock or blame an individual player, never comment on effort or character.
- No betting, odds, spreads or picks. Never read `odds`, `pickcenter`, `againstTheSpread`, `injuries`, `news`, `article`, `videos`.
- No claim of affiliation. Footer text: "Unofficial fan zine. Not affiliated with the WNBA, the NBA, any team, or our data provider."
- No em dashes in any user-facing copy or docs.
- Audio: never autoplay. Never speak text that did not pass the fact lock or come from the facts sheet. Stock Polly voices only, never a voice styled after a real announcer. The transcript is always shown next to the player.
- Do not use the Polly generative engine for the recap: AWS documents that it can occasionally produce speech that is not in the input text. Neural only.

## Model output rules
- Model output is still input. Schema check, then fact lock, then render. Anything that fails is dropped, never shown.
- Every field the model returns is rendered, and every rendered field is fact-locked. Do not add a model output field that is not checked.
- Numbers and names come from the facts sheet. The model never writes a date, score or stat that the lock did not approve.
- Do not "fix" the fact lock by loosening it. If it rejects too much, stop and report with examples.

## Security
- Jinja2 autoescape on. No `|safe` on anything model- or feed-derived. In `app.js`: `textContent` only, no `innerHTML`, no `eval`, no `new Function`.
- S3 bucket private. CloudFront OAC only. Response headers policy with CSP, HSTS, X-Content-Type-Options, frame-ancestors none.
- No account ids in tracked files, including notes about removing them. Account-specific values live in SAM parameters or `samconfig.toml` (gitignored).
- Browser storage: only the visitor's chosen team, in try/catch.
- No inbound API, no forms. If a task needs one, stop and report.

## Process
- Work block by block in tasks.md order. Each block ends with a CHECKPOINT. Do not start the next block until it passes. Record PASS or FAIL with evidence (command output, file list, URLs) in the checkpoint summary and in `LEDGER.md`.
- Propose first, wait for owner approval, then implement.
- DO NOT refactor other code. DO NOT rename files. DO NOT add dependencies not named in tech.md.
- Verify against actual files and the deployed stack, not memory. Read installed package signatures before using an API.
- If a checkpoint FAILS, fix within that block only. After two failed attempts, stop and report.
- Every checkpoint asks two questions: PASS or FAIL? Is anything from `spike/` still in use? If yes, stop and report so the owner decides promote or discard.
- No code is deleted before its `LEDGER.md` entry exists.
- Deploy (`sam deploy`) only in tasks that say so, after owner approval.

## What "discard" means
- Disposition `discard` means the code is not promoted into the product. It is **not** deleted from the
  repo. `spike/` stays committed as an artifact of how the project was built, and the README has a
  section describing it.
- Cloud resources created by a spike ARE deleted at the block's checkpoint. Files cost nothing; running
  infrastructure costs money and widens the blast radius.
- Product code never imports from `spike/`. Every checkpoint still asks whether anything in `spike/` is
  in use, and a yes stops the block.

## Attribution
- Every page credits the data provider in the footer: the words "Data from BALLDONTLIE" with
  `BALLDONTLIE` linked to `https://www.balldontlie.io`, `rel="noopener"`. Same on the About page, in
  a sentence rather than a footer line.
- The credit renders server-side, is in the HTML with JavaScript off, and is never inside a collapsed
  or hidden element.
- BALLDONTLIE's terms do not require attribution. We do it anyway, as a matter of practice. Do not
  remove it to save space, and do not treat it as optional in any template.
- The credit is a credit, never an endorsement. Never write or imply that BALLDONTLIE, the WNBA, or
  any team sponsors, endorses, partners with, or is associated with this site. The About page states
  the non-affiliation explicitly.
- Never present raw provider data as a downloadable dataset or an API of our own. The site publishes
  derived issues, not the feed.

## Build log
- `BUILD-LOG.md` is the running record of the work. `LEDGER.md` is the record of decisions and spike
  answers with their cost. They do not repeat each other. If an entry is going in both, it belongs in
  the build log, and the ledger gets only the question, the answer, the disposition and what it changed.
  Never copy the Did, Resources or Evidence lines into the ledger; reference the task id instead.
- Not every task earns a ledger entry. A ledger entry exists only for: a spike question, a decision that
  cost something or closed off an option, a rejected approach, and any code discarded.
- Maintain `BUILD-LOG.md` at the repo root. Append one entry at the end of every task, before reporting to the owner.
- Never rewrite or edit earlier entries. Append only.
- `BUILD-LOG.md` is public. It must never contain the AWS account id, any ARN that carries the account id, secrets, the BALLDONTLIE API key, prompts, or model output text.
- Entry format:
  ```
  ## <date> . <task id> . <short title>
  - Tier: <Spike|Working|Full>
  - Did: <what was done, one or two lines>
  - Result: <PASS | FAIL | the spike question's answer>
  - Resources: <cloud resources touched + tags, or "none">
  - Evidence: <commit hash, file paths, timestamps; no account id, ARN, or secret>
  ```

## What discard means
- Spike files are committed at the end of each spike task, not at the checkpoint. An uncommitted
  spike file is one `rm` away from gone, and the findings are only half the artifact.

- Never print the caller identity unmasked. `aws sts get-caller-identity` returns the account id in the
  ARN; use `--query Account` and mask all but the last four digits, or skip the check when a following
  SSM or S3 call already proves the session is live. An account id that reaches a transcript has reached
  a place it can be copied from.
- Read results from a file, not from stdout, whenever a command runs longer than a few seconds or prints
  more than a screen. Swallowed and truncated stdout has already produced one wrong conclusion (LEDGER,
  Sep 24): read the file the script wrote, and read it after the script has finished.

## Who works on this repo
Two agents commit here. Kiro builds and owns everything that touches AWS: deploys, Bedrock, Polly, SSM,
SAM, and any command that needs the `fcp` profile. Claude (in Cowork, on the same folder) takes work that
is local and in scope: templates, CSS, copy, docs, spec edits, pure-Python modules with tests, local
renders, and design review. Both follow these guardrails, both append to BUILD-LOG.md, and each marks its
own entries. Before starting a task, `git log` and read the latest BUILD-LOG entries: the other agent may
have moved things since your last session. Never revert the other agent's commit without the owner.
