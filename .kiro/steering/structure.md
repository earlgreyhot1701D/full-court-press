# Structure

One file, one responsibility. No god files. If a file starts doing two jobs, stop and report before splitting.

```
full-court-press/
  PRD.md                    source of truth for scope and gates
  LEDGER.md                 findings ledger, one entry per block and per discard
  docs/agent-prompts/OWNER-SETUP.md            steps only the owner does
  template.yaml             SAM stack
  requirements.txt          jinja2, Pillow (pinned only when a Full-tier block says so)
  .githooks/pre-commit      spike walls (see guardrails.md)
  spike/                    [THROWAWAY] Block 0 only. One flat script per question.
  src/zine/
    league_config.py        league keys, BALLDONTLIE path segments, enabled flags (NBA disabled, STUB)
    bdl_client.py           HTTP only: auth header, rate limit, 429 backoff, timeout, try/except, returns dicts
    api_key.py              reads the API key from SSM (or BDL_API_KEY locally), caches in memory.
                            (Was secrets.py: that name shadows the standard library module.)
    cache.py                read/write raw/ and facts/ in S3 or ./out in dry run
    facts.py                raw summary -> facts sheet (pure function)
    timeline.py             plays -> true game order (the feed logs some events late)
    quarters.py             plays -> points per period, must add up to the final
    pbp_stats.py            plays + rosters -> per-player stat line, with the reconciliation gates
    runs.py                 play-by-play -> scoring runs (pure function)
    game_of_night.py        interest score (pure function, rules from gotn_rules.json)
    voices.py               voice definitions (traits, banned phrases, rhythm)
    voice_client.py         Bedrock Converse call only, returns parsed JSON or None
    output_schema.py        schema check for model output
    fact_lock.py            number/name checks (pure function)
    render.py               Jinja2 -> HTML strings
    card.py                 Pillow -> PNG bytes
    audio_script.py         facts + locked headline -> the ~25 word script (pure function, no model)
    audio_client.py         Polly SynthesizeSpeech only, returns MP3 bytes or None
    league_strip.py         Around the League data (pure function)
    publish.py              write site/ files and index JSON
    state.py                last-run marker
    hunter.py               Lambda handler, orchestrates the above, no logic of its own
  src/zine/gotn_rules.json
  templates/                issue.html, today.html, archive.html, team.html, _base.html
  static/                   styles.css, print.css, app.js
  fixtures/golden/          raw summaries + facts sheets for the golden set
  fixtures/mock/            hand-written mock facts for Block 1
  tests/                    Working-tier tests (happy path + known edge cases)
```

Pure functions (`facts`, `runs`, `game_of_night`, `fact_lock`, `league_strip`) never do I/O. Only `espn_client`, `cache`, `voice_client`, `publish`, `state` touch the network or S3.
