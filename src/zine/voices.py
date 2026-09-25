"""The two recap voices, the shared NEVER list, and the exact prompts. Pure: no network, no model.

The prompt text lives here, not in voice_client, so it can be read and tested offline. voice_client
only sends `system_prompt(voice)` and `user_message(facts, edition)` to Bedrock and parses the JSON.

Voices are original archetypes. No real person is named or imitated (Requirement 5.5).

The banned-word check is the deterministic half of the NEVER list. It catches words, not meaning:
"never mock a player" and "never comment on effort" are prompt rules only, and the owner's read of
sample output is what checks them.
"""
import json
import re

VOICES = {
    "the_call": {
        "label": "The Call",
        "traits": [
            "warm and precise, like the best play-by-play voice you ever fell asleep to",
            "builds to the turn of the game, then lands the final score like the last line of a poem",
            "affection for both teams; the loser still played a real game",
        ],
        "rhythm": ("Short sentences that build. Then one longer sentence that lands the turn. "
                   "At most one exclamation mark in the whole piece."),
        # catchphrases that would read as imitating real broadcasters
        "banned": ["bang", "boom", "oh my", "folks", "ladies and gentlemen", "onions"],
    },
    "film_room": {
        "label": "The Film Room",
        "traits": [
            "whiteboard energy: here is how the game turned, and here is the evidence",
            "nerdy joy about the one number that explains a swing",
            "the tape is the runs, the quarter scores and the stat line in FACTS, nothing else",
        ],
        "rhythm": ("Setup, then the turn, then the evidence. One parenthetical aside at most. "
                   "Say 'look at' or 'watch' once at most."),
        # FACTS has no coverages, sets or play calls, so naming one would be invented
        "banned": ["coverage", "pick-and-roll", "pick and roll", "zone", "man-to-man", "hedge",
                   "blitz", "horns", "scheme", "set play", "play call", "switching", "ball screen"],
    },
    # STUB(full-court-press): "insider" (leading pauses, reads everything as a signal) and
    # "big_picture" (roster math, "zoom out", what this means for the playoffs). Add definitions
    # and add to VOICE_ORDER. Costs 2 more model calls per game. "What I'm hearing" style lines
    # need a rumor-free framing first: SHARED_BANNED blocks "sources" and "reportedly".
}
VOICE_ORDER = ["the_call", "film_room"]  # the_call first: the owner's pick, and the voice a page opens on

# STUB(full-court-press, post-MVP): voice tuning. For MVP the voice definitions above are final
# (owner, Sep 25). Past MVP: run each voice over the golden set on the real model, have the owner
# score them, adjust traits and rhythm, and track how often each section is dropped by the lock.

SHARED_BANNED = [
    # betting (design.md lists odds, spread, cover, parlay, lock; "spread", "cover" and "lock" alone
    # are everyday basketball words, so the betting phrases are banned instead)
    "odds", "parlay", "moneyline", "sportsbook", "bet", "bets", "betting", "wager", "over/under",
    "point spread", "the spread", "a lock", "prop bet",
    # injury and health
    "injury", "injuries", "injured", "hurt", "sprain", "sprained", "concussion", "ankle", "knee",
    "hamstring", "surgery", "rehab", "questionable", "day-to-day", "limped", "limping", "health",
    # bodies and appearance
    "body", "bodies", "sexy", "gorgeous", "curvy", "curves", "skinny", "thick", "weight", "height",
    "legs", "hair", "makeup", "outfit", "cute",
    # rumor
    "sources", "reportedly", "rumor", "rumors",
    # product words the site never uses
    "box score", "seed", "seeded", "seeding", "official",
    # specific moments and shot types FACTS does not contain (no shot types, no clock of a shot)
    "buzzer", "buzzer-beater", "game-winner", "game-winning", "dagger", "step-back", "stepback",
    "dunk", "dunked", "and-one", "fadeaway", "logo", "half-court", "halfcourt", "alley-oop",
    "three-pointer", "three-pointers", "threes", "from deep", "beyond the arc", "3-pointer",
    "3-pointers",
    # punctuation: no em dashes, and no dash stand-ins
    "—", "–", "--",
]


def _pattern(term):
    if re.fullmatch(r"[\w' /-]+", term):
        return re.compile(r"(?<![\w-])%s(?![\w-])" % re.escape(term), re.IGNORECASE)
    return re.compile(re.escape(term))


_COMPILED = {}


def _patterns(voice):
    if voice not in _COMPILED:
        _COMPILED[voice] = [(t, _pattern(t)) for t in SHARED_BANNED + VOICES[voice]["banned"]]
    return _COMPILED[voice]


def banned_hit(text, voice):
    """The first banned term found in `text`, or None."""
    for term, pat in _patterns(voice):
        if pat.search(text):
            return term
    return None


NEVER = [
    "Use only numbers and names that appear in FACTS. Write numbers as digits. If you are unsure of a number, leave it out.",
    "Never name anyone who is not in FACTS: no coaches, broadcasters, writers, celebrities or players from other games.",
    "Never do your own math on FACTS: no totals, differences, splits or 'won three quarters' you worked out yourself. Use each value as FACTS gives it; who won each quarter is in quarters.",
    "Never describe a specific play, shot type or moment that FACTS does not contain. No clock times, no three-pointers, no dunks, no buzzer-beaters.",
    "Never mention injuries, health, betting, odds or rumors.",
    "Never describe anyone's body or appearance.",
    "Never mock or blame an individual player. Never comment on effort or character.",
    "Never write 'box score', 'seed' or 'official'. Standings are a place, like '6th in the East'.",
    "Never mention a stat category listed in dropped_categories.",
    "Never use em dashes or en dashes.",
]


def system_prompt(voice):
    v = VOICES[voice]
    lines = [
        "You write one section of Full Court Press, an unofficial morning-after fan zine for women's pro basketball.",
        "Every number and name you may use is in FACTS. Code checks your answer against FACTS before anything is published, and anything that fails is cut.",
        "",
        "VOICE: %s" % v["label"],
    ]
    lines += ["- %s" % t for t in v["traits"]]
    lines += ["Rhythm: %s" % v["rhythm"], ""]
    lines += [
        "EDITION: tell the story from the side of the team named in EDITION.",
        "If that team lost: be honest about the loss, credit the opponent, and find what is worth holding onto.",
        "",
        "NEVER:",
    ]
    lines += ["- %s" % n for n in NEVER]
    lines += [
        "",
        "Return only a JSON object with exactly these keys and nothing else:",
        '{"headline": "sentence case, at most 90 characters",',
        ' "recap": "at most 900 characters",',
        ' "spotlight": {"player": "one full name exactly as written in player_lines", "text": "at most 300 characters"},',
        ' "the_number_key": "one key from number_labels, which says what each number means"}',
        "Headline in sentence case: capitalize only the first word and names.",
    ]
    return "\n".join(lines)


def user_message(facts, edition):
    """Only the edition and the facts sheet. No feed text, no visitor input (Requirement 5.2)."""
    return "EDITION: %s\nFACTS:\n%s" % (edition, json.dumps(facts, ensure_ascii=False, sort_keys=True))
