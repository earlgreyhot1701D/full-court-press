# Findings ledger

One entry per block, per spike question, and before any code is discarded. Keep wrong versions: the correction is the interesting part.

## Entry template
```
### <date> . Block <n> . <short title>
Question:     <what we needed to know>
Answer:       <yes / no / PASS / FAIL, with evidence>
Cost:         <time, attempts>
Disposition:  <discard | promote | shelve (branch + hash)>
Changes PRD?: <no | yes: what>
```

## Entries

### 2026-09-20 . Block 0 . Compliance gate: data source
Question:     Can we pull WNBA box scores from ESPN's site API on a schedule and feed them to a model?
Answer:       No. The Disney/ESPN Terms of Use prohibit accessing or extracting content "using a robot, spider, script, or other automated means, including... for the purposes of creating or developing any AI Tool, data mining or web scraping", license content for "personal, noncommercial use only", and bar building a dataset from it. www.espn.com/robots.txt disallows */boxscore? and */playbyplay? for all user agents and blocks several AI crawlers outright. site.api.espn.com returns Access Denied for robots.txt, so there is no permission to rely on there either.
Replacement:  BALLDONTLIE. Terms Section 6 expressly permits use, caching, storage, publishing, derivative works and "artificial intelligence and machine-learning training or outputs", with no attribution required. Restrictions we must respect: do not build a product that competes with BALLDONTLIE, do not resell raw data, do not imply official league or BALLDONTLIE endorsement.
Cost:         Free tier covers games. Player stats need ALL-STAR ($9.99/mo per sport). Standings and plays need GOAT ($39.99/mo), so both are STUBs.
Disposition:  promote (spec updated: tech.md, design.md, requirements 2/3/9, tasks 0.2/0.4/2.x/5.1, PRD)
Changes PRD?: yes. Data source, quarter-based game flow, STUBs for runs and standings, API key in SSM, data cost line.
