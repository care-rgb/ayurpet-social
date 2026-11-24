# AyurPet Social Engine: notes for Claude (merged into ayurpet-social, 24 Nov 2026)

Source: ayurpet-social-engine.zip shared by the team. Lives in `engine/` here. Read-only against Meta (outliers, scorecard).
Pages: @ayurpetofficial (India, 17841472849482734) and @ayurpet_global (17841465833626335).
Goal: 10,000 followers combined by 22 Dec 2026 (about 145 a day). Optimise for sends per reach, watch time, then saves.

## How to run
- Token: env `META_IG_TOKEN` (set on this laptop). Never print or write it. Python stdlib only. Use `PYTHONUTF8=1 python`.
- `python engine/scripts/outliers.py [--days 60] [--check]` -> `engine/research/outliers/OUTLIERS_<date>.md/.csv`. Takes several minutes (89 pages).
- `python engine/scripts/scorecard.py [--days 30]` -> `engine/ledger/SCORECARD_<date>.md`, appends `followers.csv`.
- `engine/watchlist.csv`: add pages as `handle,market,lane,note`; run `--check` after. Personal accounts cannot be read.
- Weekly rhythm: Monday outliers + scorecard, tag last week's posts in `ledger/tags.csv`; Tuesday plan briefs (`briefs/TEMPLATE.md`);
  Wed to Sun make and post about 5 reels + 2 carousels per page. Prompts in `engine/docs/PROMPTS.md`, rules in `engine/docs/PLAYBOOK.md`.

## Our rules still apply (they override the zip's "no sign-off" line)
- Nothing is posted, scheduled, sent or commented without Kainaat's yes in chat. Karan's 20 Nov ruling: she is the approver.
- Copy the mechanism, never the video. Our own dogs and footage. Brand rules (plain words, no em dashes, no medical claims, "6,000+ reviews",
  no Diwali on global, AI images labelled) unchanged. One post per account per day, 2 max.
- Reel covers (Kainaat, 24 Nov): every reel cover, especially the animated ones, is made in AyurPet brand language (same colours, fonts and
  layout family as the new carousel style) so the profile grid reads as one feed. Set the cover explicitly; never leave a random frame.

## Links to the rest of the system
- Daily DM/comment engagement: `docs/ENGAGEMENT.md`, `scripts/engage.py`.
- Posting: `calendar/schedule.json` and `calendar/reels.json` (cloud auto-poster), `scripts/ig.py`.
