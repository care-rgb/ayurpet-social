# Session handoff

## 2026-11-23 (built, handed to the social team)
- Built: scripts/meta.py, outliers.py, scorecard.py (Python standard library only, read-only on Meta), watchlist.csv (90 pages across India, global and UAE), README, CLAUDE.md, docs/PLAYBOOK.md, docs/PROMPTS.md, briefs/TEMPLATE.md, ledger files.
- Live check before hand-over: business_discovery read headsupfortails, supertails.official, dogseechew and indian.tommy fine. drools_india, wigglesindia and zigly_pets were wrong handles; they are now droolsindia, wiggles.in and ziglyforpets (taken from the brands' own sites, not yet checked against Meta). Rows marked "(unconfirmed)" in watchlist.csv came from web research only. `--check` on the first run will flag any that are wrong. A cut-short response crashed the first check, so meta.py now retries those.
- Both scripts were tested offline with fake data (all code paths, including a bad handle and a refused metric). They have not been run end to end against Meta. The first real run belongs to the social team, on their own machine or in the cloud env.
- Local git only. Not pushed anywhere yet.
