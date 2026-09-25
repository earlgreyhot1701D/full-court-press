# Runs the hand-written stand-in samples in voice-samples-25071.md through voice_run.check.
# From the repo root: python design/voice_samples_check.py
import json, sys
sys.path[:0] = ["src", "tests"]
from test_facts_gotn import golden_facts
from zine import voice_run
f = golden_facts()["25071"]
print("max blk:", sorted(((l.get("blk", 0), l["player"]) for l in f["player_lines"]), reverse=True)[:3])
S = {
 "call_PHX": ("the_call", {
  "headline": "Down 14, the Mercury found a way by 1",
  "recap": "Dallas had this one. The Wings led by 14, and Paige Bueckers kept answering with 30 points of her own. Then the 4th quarter came, and Phoenix won it 26-18. Kahleah Copper made 10 free throws on the way to a game-high 31. Alyssa Thomas ran the whole thing: 15 points, 11 rebounds, 12 assists. Final in Phoenix: Mercury 87, Wings 86, and every one of those points mattered.",
  "spotlight": {"player": "Alyssa Thomas", "text": "Thomas ran the offense and cleaned the glass: 15 points, 11 rebounds, 12 assists. A triple-double, and the steadiest line on the floor in a 1-point game."},
  "the_number_key": "winner_max_deficit"}),
 "film_PHX": ("film_room", {
  "headline": "How Phoenix erased 14 and won the 4th 26-18",
  "recap": "The quarter scores tell the story. Dallas took the 1st 26-19 and the 3rd 21-18, with an 8-0 run in the middle of it (the only run of the game long enough to make the sheet). Phoenix took the 2nd 24-21, then the 4th 26-18, and that last one was the game. Now the evidence. Kahleah Copper got her 31 from 10 field goals and 10 free throws. Alyssa Thomas added the triple-double. Dallas came up 1 short, 87-86.",
  "spotlight": {"player": "Kahleah Copper", "text": "Copper's 31 is the nerdiest line on the sheet: 10 made field goals, 10 made free throws. In a 1-point game, every one of those free throws counts."},
  "the_number_key": "q4_home"}),
 "call_DAL": ("the_call", {
  "headline": "Bueckers gave Dallas 30, and it came down to 1",
  "recap": "Some nights you do almost everything right. Dallas took the 1st quarter 26-19, built a 14-point lead, and still led going into the 4th. Paige Bueckers scored 30 and handed out 7 assists. Jessica Shepard pulled down 19 rebounds to go with 17 points. Phoenix had the last word, 26-18 in the 4th, and won 87-86. The Wings are still 4th in the West at 27-17, and that is worth holding onto.",
  "spotlight": {"player": "Jessica Shepard", "text": "Shepard owned the glass: 19 rebounds, 17 points and 6 assists. A double-double in a 1-point loss is still a double-double."},
  "the_number_key": "jessica_shepard_reb"}),
 "film_DAL": ("film_room", {
  "headline": "The Wings won the 1st and 3rd, and lost the 4th 26-18",
  "recap": "The quarter scores make the case. Dallas took the 1st 26-19 and the 3rd 21-18, with an 8-0 run in the 3rd. Phoenix took the 2nd 24-21 and then the 4th 26-18, and that last one decided it. There was plenty on the Wings' side of the sheet (Awak Kuier blocked 5 shots). Paige Bueckers made 12 field goals on her way to 30. Kahleah Copper answered with 10 field goals and 10 free throws for 31, and Dallas fell 87-86.",
  "spotlight": {"player": "Awak Kuier", "text": "Kuier finished with 5 blocks, the most in the game, plus 8 points and 5 rebounds."},
  "the_number_key": "awak_kuier_blk"}),
 "CAUGHT_spelled": ("film_room", {
  "headline": "Dallas won three of four quarters and still lost",
  "recap": "x", "spotlight": {"player": "Awak Kuier", "text": "x"}, "the_number_key": "margin"}),
 "CAUGHT_moment": ("the_call", {
  "headline": "Copper's dagger sinks Dallas 87-86",
  "recap": "x", "spotlight": {"player": "Awak Kuier", "text": "x"}, "the_number_key": "margin"}),
 "MISSED_wrong_claim": ("film_room", {
  "headline": "Dallas won the 1st, 2nd and 3rd and still lost",
  "recap": "x", "spotlight": {"player": "Awak Kuier", "text": "x"}, "the_number_key": "margin"}),
}
for k, (v, out) in S.items():
    r = voice_run.check(out, f, v)
    print(k, "OK" if r["ok"] else json.dumps(r["sections"]))
    for s in ("headline","recap"):
        print("  ", s, len(out[s]))
    print("   spot", len(out["spotlight"]["text"]))
