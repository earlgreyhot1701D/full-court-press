# Full Court Press: demo narration

About 75 seconds, read at a relaxed pace. The video is recorded from the live site at 1x speed,
no audio, so you add this voiceover in your editor. Timestamps are approximate: slide each line
to where its shot starts. Say what it means, not what's being clicked.

| Time | On screen | Say |
|---|---|---|
| 0:00 | Front page: ransom masthead, Thursday Sep 24, the cards | This is Full Court Press, the zine for last night's WNBA games. Every morning at 6:15, a Lambda finds the finals and prints an issue for every game. |
| 0:08 | Scroll the slate, tap the Sun tab | Pick your team. |
| 0:12 | Sun edition cover, then the recap (The Call) | The score, The Number and every stat are counted by code from the play-by-play. The AI only writes the voice. This one is The Call. |
| 0:23 | The Film Room | Same facts, second voice. The Film Room goes quarter by quarter, evidence first. |
| 0:31 | Tempo edition | And the team that lost gets its own edition, told from their side. Honest about the loss. |
| 0:39 | The stat line, then the quarters | Every one of these numbers was counted from every single play, and each team's points have to add up to the final score before anything prints. |
| 0:47 | Print view: the 8-panel sheet | Hit print, and the whole issue folds into an eight-panel pocket zine. |
| 0:53 | Valkyries page, the code-written recap | This is the part I care about most. Every sentence the AI writes is checked against the facts. The AI recap on this page didn't pass, so we cut it, and code wrote a plain one instead. The page tells you that. |
| 1:05 | About: How we check the numbers | How we check, and what the checks can't prove, is right on the About page. |
| 1:10 | Back to the front page | Lambda, Bedrock, Polly, S3 and CloudFront. Live at fullcourtpress dot lol. I directed, the agents built, and I validated and decided. AI Assisted. Human Approved. Powered by NLP. |

## If you run long

Cut in this order: the 0:08 line, then the second sentence at 0:39. Keep 0:53 and the close.

## Numbers to keep consistent with the article and README

- 56 issue pages across four nights, Sep 21 to 24
- 36 AI recaps, 20 code-written recaps, 0 empty (after the Sep 27 redeploy)
- Points reconcile to the final score in every game; other stats are counted, not independently verified

## Don't

- Don't speed up the footage past 1x. The site is fast enough.
- Don't read the recaps aloud. Let the viewer read for a beat.
- Don't claim the AI never makes mistakes. The whole pitch is that it does, and the site catches it.
