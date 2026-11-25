# Session handoff

## 2026-11-23 (built, handed to the social team)
- Built: scripts/meta.py, outliers.py, scorecard.py (Python standard library only, read-only on Meta), watchlist.csv (90 pages across India, global and UAE), README, CLAUDE.md, docs/PLAYBOOK.md, docs/PROMPTS.md, briefs/TEMPLATE.md, ledger files.
- Live check before hand-over: business_discovery read headsupfortails, supertails.official, dogseechew and indian.tommy fine. drools_india, wigglesindia and zigly_pets were wrong handles; they are now droolsindia, wiggles.in and ziglyforpets (taken from the brands' own sites, not yet checked against Meta). Rows marked "(unconfirmed)" in watchlist.csv came from web research only. `--check` on the first run will flag any that are wrong. A cut-short response crashed the first check, so meta.py now retries those.
- Both scripts were tested offline with fake data (all code paths, including a bad handle and a refused metric). They have not been run end to end against Meta. The first real run belongs to the social team, on their own machine or in the cloud env.
- Local git only. Not pushed anywhere yet.

## 2026-11-25 (Kainaat session)
- Adapted the @doggoslab mechanism (myth-correcting hook, one reason, three fixes, save-and-send) into an India 2D reel: "Your dog doesn't need more toys. He needs a routine." Brief: briefs/2026-11-25_ayurpetofficial_routine-not-toys.md.
- Built in Remotion at ~/Documents/claude/ayurpet-2d (local, not in git): flat 2D dog, toys, day cycle, yak chew and the official pouch. Narration: ElevenLabs "Lara" (stand-in female voice; Kainaat's own voice is not cloned yet). Scenes are timed to the voice. Rendered 21 s file is reels/2026-11-25_routine-not-toys_v1-in.mp4 with cover.
- Calendar entry added as HOLD, not scheduled. Nothing posted.
- Gotchas on this laptop: npm install scripts fail (a stray env value is used as a program name), so install with --ignore-scripts and run Remotion with `node node_modules/@remotion/cli/remotion-cli.js`. PowerShell 5.1 `Set-Content -Encoding utf8` adds a BOM that breaks package.json. ayurpet-reels is diverged from origin (10 ahead, 37 behind): do not pull there without resolving TASKS.md and SESSION_HANDOFF.md conflicts.
