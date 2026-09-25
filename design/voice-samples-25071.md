# Voice samples: game 25071 (Mercury 87, Wings 86)

**Read this first.** Claude wrote these by hand as stand-ins, not Haiku. The real model call gets wired in during Kiro's one Bedrock session. Every sample below went through the real checks (`voice_run.check`: schema, fact lock, banned words) against the real facts sheet. Claude also checked every claim by hand against the facts.

What you're judging: **do the two voices feel different, and would a fan want to read them?** Mark anything that sounds off. The prompts are in `src/zine/voices.py`.

---

## The Call . Phoenix edition (winner)

**Down 14, the Mercury found a way by 1**

Dallas had this one. The Wings led by 14, and Paige Bueckers kept answering with 30 points of her own. Then the 4th quarter came, and Phoenix won it 26-18. Kahleah Copper made 10 free throws on the way to a game-high 31. Alyssa Thomas ran the whole thing: 15 points, 11 rebounds, 12 assists. Final in Phoenix: Mercury 87, Wings 86, and every one of those points mattered.

*Spotlight, Alyssa Thomas:* Thomas ran the offense and cleaned the glass: 15 points, 11 rebounds, 12 assists. A triple-double, and the steadiest line on the floor in a 1-point game.

*The Number:* 14 (point deficit the Mercury came back from)

---

## The Film Room . Phoenix edition (winner)

**How Phoenix erased 14 and won the 4th 26-18**

The quarter scores tell the story. Dallas took the 1st 26-19 and the 3rd 21-18, with an 8-0 run in the middle of it (the only run of the game long enough to make the sheet). Phoenix took the 2nd 24-21, then the 4th 26-18, and that last one was the game. Now the evidence. Kahleah Copper got her 31 from 10 field goals and 10 free throws. Alyssa Thomas added the triple-double. Dallas came up 1 short, 87-86.

*Spotlight, Kahleah Copper:* Copper's 31 is the nerdiest line on the sheet: 10 made field goals, 10 made free throws. In a 1-point game, every one of those free throws counts.

*The Number:* 26 (Mercury points in the 4th)

---

## The Call . Dallas edition (the losing side)

**Bueckers gave Dallas 30, and it came down to 1**

Some nights you do almost everything right. Dallas took the 1st quarter 26-19, built a 14-point lead, and still led going into the 4th. Paige Bueckers scored 30 and handed out 7 assists. Jessica Shepard pulled down 19 rebounds to go with 17 points. Phoenix had the last word, 26-18 in the 4th, and won 87-86. The Wings are still 4th in the West at 27-17, and that is worth holding onto.

*Spotlight, Jessica Shepard:* Shepard owned the glass: 19 rebounds, 17 points and 6 assists. A double-double in a 1-point loss is still a double-double.

*The Number:* 19 (rebounds for Jessica Shepard)

---

## The Film Room . Dallas edition (the losing side)

**The Wings won the 1st and 3rd, and lost the 4th 26-18**

The quarter scores make the case. Dallas took the 1st 26-19 and the 3rd 21-18, with an 8-0 run in the 3rd. Phoenix took the 2nd 24-21 and then the 4th 26-18, and that last one decided it. There was plenty on the Wings' side of the sheet (Awak Kuier blocked 5 shots). Paige Bueckers made 12 field goals on her way to 30. Kahleah Copper answered with 10 field goals and 10 free throws for 31, and Dallas fell 87-86.

*Spotlight, Awak Kuier:* Kuier finished with 5 blocks, the most in the game, plus 8 points and 5 rebounds.

*The Number:* 5 (blocks for Awak Kuier)

---

## What the checks caught, and what they missed

| Line | Result | Why |
|---|---|---|
| "Dallas won three of four quarters and still lost" | Caught | "three" is a spelled-out number |
| "Copper's dagger sinks Dallas 87-86" | Caught | "dagger" claims a specific moment the facts don't have |
| "Dallas had this one" (Claude's own draft) | Caught, then allowed | "one" used as a pronoun. Allowlist widened: this one, that one, last one, the one, each one |
| **"Dallas won the 1st, 2nd and 3rd and still lost"** | **Missed** | False: Phoenix won the 2nd, 24-21. Every number in it exists somewhere in the game. |
| **"Copper split her 31 right down the middle: 10 field goals, 10 free throws"** (Claude's own draft) | **Missed** | False: 10 field goals is at least 20 points. Claude caught it by hand. |

Both misses come from the model doing its own math on the facts. The lock can't see that, so the prompt now says so outright: "Never do your own math on FACTS." That's a rule for the model, not a guarantee. The honest line for the About page: the lock proves every number and name came from our facts. It doesn't prove the sentence around them is right.
