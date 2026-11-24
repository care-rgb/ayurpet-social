# AyurPet Social Engine

Finds the posts that are blowing up on other pages, works out why, and turns that into our next posts. Then it checks which of our own posts won, so we do more of those.

For: the AyurPet social team. You run it end to end. No sign-off needed from anyone.
Pages: @ayurpetofficial (India) and @ayurpet_global (global).
Goal: 10,000 followers combined by 22 Dec 2026. We need about 145 new followers a day, so every post has to earn reach.

## What's in here

| File | What it is |
|---|---|
| `watchlist.csv` | Pages we study. Add as many as you like (see below). |
| `scripts/outliers.py` | Weekly pull. Shows every post on those pages that did 3x, 5x or 10x its own page's normal. |
| `scripts/scorecard.py` | Weekly check on our own posts: views, shares, saves, watch time, follows, and which ones won. |
| `docs/PLAYBOOK.md` | How virality works on Instagram right now, and the formats and hooks to copy. Read this first. |
| `docs/PROMPTS.md` | Copy-paste prompts for Claude for each step of the week. |
| `briefs/` | One brief per post we're making. Start from `briefs/TEMPLATE.md`. |
| `ledger/` | Scorecards, `tags.csv` (what each of our posts was), `WINNERS.md`, `LEARNINGS.md`. |
| `research/outliers/` | Each week's outlier list. |

## Set up once (10 minutes)

1. Install Python 3 if the laptop doesn't have it (python.org). Nothing else to install.
2. Get this folder onto your laptop (clone the repo or copy the folder).
3. Get the Meta token from whoever manages AyurPet's Meta Business account. It's the same token the posting script `ig.py` uses. Keep it in your password manager, never in a chat, a doc or this folder.
4. Put it in your terminal before running anything:
   - Mac: `export META_IG_TOKEN='paste-token-here'`
   - Windows (PowerShell): `$env:META_IG_TOKEN='paste-token-here'`
5. Check the watch list works: `python3 scripts/outliers.py --check` (Windows: `python` instead of `python3`). Any page it can't read is a wrong handle or a personal account. Fix the handle or delete the line.

Running it from a Claude Code cloud session in the "AyurPet Reels" environment also works. There the token is already set up as `proxy`, so skip steps 3 and 4.

## Adding pages to study

Open `watchlist.csv` in Excel, Numbers or Google Sheets (download as CSV) and add a row:

`handle,market,lane,note`

- handle: the Instagram username without @
- market: `in` (India), `gl` (global), `ae` (UAE) or `both`
- lane: `creator`, `pet brand`, `vet creator`, `ayurveda` or `meme page`
- note: why you're watching it, in a few words

Or just tell Claude: "add @somehandle to the watch list, India, creator". Then run `--check` so you know Meta can read it. Only business and creator accounts can be read. Most brands and big creators are.

Good places to find new pages: the accounts that comment on viral dog reels, the "suggested for you" row on a creator's profile, Reels that keep showing up in your feed, and the pages our winners got shared to.

## The week

| Day | Do this | Takes |
|---|---|---|
| Monday | Run both scripts. Open the outlier list, watch the top 10 with sound, fill in the hook, format and why for each one. | 1 hour |
| Monday | Read our scorecard. Tag last week's posts in `ledger/tags.csv`. Move winners to `WINNERS.md` and anything learned to `LEARNINGS.md`. | 30 min |
| Tuesday | Pick the week's posts: about half are new versions of our own winners, 4 in 10 copy the mechanism of a 5x+ outlier, the rest are wild new tests. Write a brief for each. | 1 hour |
| Wed to Sun | Make and post. About 5 reels and 2 carousels a page a week. Put 1 or 2 reels a week out as Trial Reels (they go to non-followers first). | daily |

Commands:

```
python3 scripts/outliers.py              # outliers from the last 30 days
python3 scripts/outliers.py --days 60    # first run, or a quiet week
python3 scripts/scorecard.py             # our own posts, last 30 days
```

The prompts for each step are in `docs/PROMPTS.md`.

## How it judges a post

- Other pages: a reel is scored on views against that page's own median reel views. A carousel or photo is scored on likes against the page's median likes (Meta doesn't share other pages' feed views). 3x = signal, 5x = strong, 10x = breakout. We compare a page with itself, so a 20k page's 10x post counts as much as a 2M page's.
- Our pages: views against our own normal for that type, and keep rate (shares + saves per 100 people reached). Shares are the strongest sign Instagram will push a post to people who don't follow us.

Everything here only reads data. Nothing in these scripts posts, edits or deletes anything.
