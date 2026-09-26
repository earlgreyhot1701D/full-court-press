"""The 10-second audio script (Req 16.1). Pure. No model writes anything here: the script is the
final score, overtime if any, the fact-locked headline, and the game-high scorer, from the facts
sheet. At most 30 words; if longer, the last sentence goes, then the headline."""
from zine.pagekit import winner_loser

MAX_WORDS = 30


def build(f, headline=None):
    w, l = winner_loser(f)
    s1 = "%s %d, %s %d%s." % (w["team"], w["score"], l["team"], l["score"],
                              ", in overtime" if f.get("overtime_periods") else "")
    parts = [s1]
    if headline:
        parts.append(headline.rstrip(".!?") + ".")
    high = next((n for n in f.get("notable", []) if n["type"] == "game_high"), None)
    if high:
        parts.append("%s led everyone with %s." % (high["player"], high["detail"]))
    if len(" ".join(parts).split()) > MAX_WORDS and high:
        parts.pop()                      # drop the last sentence first
    if len(" ".join(parts).split()) > MAX_WORDS and len(parts) > 1:
        parts = [s1]                     # then the headline; the score always stays
    return " ".join(parts)
