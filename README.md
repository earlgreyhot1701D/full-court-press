# Full Court Press

The zine for last night's WNBA games. An unofficial fan zine. Every finished game gets an issue, written from **each team's side**, not just the winner's, in two voices, with a share card, a 10-second audio recap, and a print button that folds the issue into an 8-panel pocket zine.

**Live:** https://dfph64wiizg5i.cloudfront.net/
**Golden set** (five real games, always there for judges): https://dfph64wiizg5i.cloudfront.net/golden/index.html

Unofficial fan zine. Not affiliated with, endorsed by, or associated with the WNBA, any team, or our data provider. Data from [BALLDONTLIE](https://www.balldontlie.io).

Built for the AWS Builder Center "Zero to Shipped" hackathon, September 2026.

---

## How it's made

Deterministic structure, AI flavor. Code writes every number. The AI writes the voice, and code checks it.

```
EventBridge Scheduler, 6:15am Pacific
  -> Lambda (the hunter)
       finds last night's finals (BALLDONTLIE)
       counts every stat from the play-by-play          code, never the model
       builds a facts sheet + plain_facts sentences     code
       asks Claude Haiku 4.5 (Bedrock) for 2 voices x 2 editions
       fact lock + banned words, retry once, else drop the section
       share card (Pillow), audio (Polly neural, script built by code)
       writes a static site to private S3
  -> CloudFront (OAC, CSP, HSTS) -> you
```

- **Stats are counted, not bought.** The data tier this project pays for has no box score, so `pbp_stats.py` counts points, rebounds, assists, steals and blocks from the play-by-play text. Every team's points must add up to the final score or the stat line is dropped. Other categories are dropped one by one if their count cannot be trusted.
- **The fact lock** (`fact_lock.py`) rejects any number or name the model writes that is not in that game's facts sheet, spelled-out numbers included. A section that fails twice is dropped and the page says "The writers' room passed on this one."
- **plain_facts.** Human audits of live model output found the lock passing sentences whose numbers were all real but whose claims were wrong ("the fourth quarter belonged to Atlanta" when Indiana won it). The fix was not a stricter prompt. Code now writes those claims itself (who won each quarter, the score at halftime, each team run, who led each team, where the standings sit) and the model quotes them.
- **Two voices:** The Call (default) and The Film Room. Original archetypes; no real person is named or imitated.
- **Every edition:** a fan of the losing team gets her own edition, told from her side, honest about the loss.

### How the numbers are checked

Points are checked by arithmetic: they must add up to the final score, which comes from a separate record. In the golden set, 5 of 5 games reconciled, overtime included, with zero plays the counter could not attribute.

The other categories have no independent source. So I checked three counted stat lines by eye against Basketball Reference on Sep 24, including Alyssa Thomas's triple-double (15 points, 11 rebounds, 12 assists), built entirely on counted rebounds and assists. All three matched.

> A human checking an agent's counting against an outside source is the best proof of the whole approach.

What that does not prove: rebounds and assists are still counted, not verified, on any given night.

## Honest limitations

- **Unofficial data feed.** Stats are counted from play-by-play text. Points reconcile; other categories are sanity-checked, not verified. A category that fails its check is left out and the page says so.
- **The lock checks numbers and names, not meaning.** It proves every number and name came from the facts. It cannot prove a sentence uses them correctly. plain_facts make that rare; they do not make it impossible.
- **Two voices, WNBA only.** Two more voices and the NBA are stubbed (below).
- **The audio is plain.** Polly neural reads a script built by code, on purpose: the generative engine can say words that are not in the script.

## Built by two agents and a human

I direct, validate and decide. Kiro (AWS's spec-driven agent) built the spec, the spikes and everything that touches AWS: the connection, the deploy, Bedrock, Polly, the API key in Parameter Store. Claude built the application code on disk, the tests and the design passes after a Kiro credit crunch mid-sprint. Each agent logs its own work in [BUILD-LOG.md](BUILD-LOG.md). Decisions and findings, including the wrong turns, are in [LEDGER.md](LEDGER.md). The deploy runbook is [DEPLOY.md](DEPLOY.md).

Security: no IAM users or access keys; the API key lives only in SSM and never passed through an agent; logs hold ids, counts and lock results only, never prompts, model text or keys; private bucket behind CloudFront OAC; CSP with no outside hosts; $10 and $2 budgets on the project tag and on Polly.

## The spikes

Before any product code existed, each risky question got a throwaway script with a pass/fail answer. They are kept in [`spike/`](spike/) as evidence that the questions got asked first. **None of it is used by the product**, and every checkpoint checked that.

| Spike | Question | Answer |
|---|---|---|
| `bdl_from_lambda.py` | Does the data API answer from an AWS Lambda, and which endpoints does the free tier allow? | Yes. Only games on the free tier; player stats, standings and plays returned 401. Led to the ALL-STAR upgrade decision. |
| `bdl_allstar_probe.py`, `bdl_routes_probe.py` | After the upgrade, is a 401 "your plan doesn't include this" or "wrong address"? | Plan, confirmed across routes. The WNBA tier table differs from the NBA one: plays and standings yes, player stats no. So stats are counted from plays. |
| `card_in_lambda.py` | Does Pillow plus a bundled font render a 1200x630 card inside Lambda? | Yes (Pillow 12.2, Python 3.13). |
| `mp3_duration.py` | Does Polly neural work in the same region, and how long is a 25-word line? | Yes. 23 words = 6.8 s, so about 30 words for a 10-second recap. |
| `golden-discovery/` | Which real 2026 games make a good golden set, including an overtime game? | Five games, one in overtime (25014). |

Each has a matching entry in [LEDGER.md](LEDGER.md) under Block 0.

## Run it locally

```
pip install -r requirements-dev.txt
PYTHONPATH=src:tests python -m pytest            # 170+ tests, offline, no AWS
PYTHONPATH=src python -m zine.dev_render_golden  # the golden site into out-golden/
PYTHONPATH=src python -m zine.dry_run --date 2026-09-22   # the hunter on fixtures, no model, no AWS
```

Deploying is in [DEPLOY.md](DEPLOY.md).

## Stubs (not built, on purpose)

- **NBA.** `league_config.py` has it disabled. Reactivate when the NBA regular season starts (late October 2026): enable it, add `nba` to `LEAGUES`. Same data shapes.
- **Two more voices**, The Insider and The Big Picture (`voices.py`).
- **Voice tuning** on real output, with drop rates tracked per voice.
- **One run at a time** via an S3 lock (a new account's Lambda concurrency is 10, so reserved concurrency is not possible).
- **Zine design stretch:** photocopy grain, crooked cards, cut-out masthead, rubber stamps.
- **Tip jar** on the About page.

## Credits

Data from [BALLDONTLIE](https://www.balldontlie.io). Fonts: Alfa Slab One, Archivo and Caveat, all SIL Open Font License, licenses in `static/fonts/`. The name is a hand-me-down from an old courthouse newsletter.

AI Assisted. Human Approved. Powered by NLP.
