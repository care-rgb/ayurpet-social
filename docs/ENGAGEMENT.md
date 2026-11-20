# AyurPet daily engagement system (set up 20 Nov 2026)

Owner and only approver: Kainaat (Karan, 20 Nov 2026: she needs no approval from him). Nothing is sent, replied or commented
until she says yes in chat. Tool: `scripts/engage.py` (uses the same Meta token as `ig.py`). Accounts: @ayurpetofficial (India),
@ayurpet_global (US/UK/world).

## What the Meta API can and cannot do (tested 20 Nov 2026 with our token)
| Job | API | How we do it |
|---|---|---|
| Read DMs, including story mentions (a signed link to the story, valid 24 h) | yes | `engage.py inbox` |
| Send a DM | only within 24 h of the person's last message | `engage.py dm-send` |
| DM after 24 h, or a first DM to someone who never wrote | no | by hand in the Instagram app |
| Read comments on our posts and reply | yes | `engage.py comments`, `reply` |
| Pin or like a comment, follow | no | by hand in the app |
| Posts that tag us or collab with us | yes | `engage.py tags` |
| Recent posts of another business or creator account | yes, public business and creator accounts only | `engage.py watch`, `watch-all` |
| Private or personal accounts | no | marked `manual` in the targets file |
| Comment on OTHER accounts' posts | no endpoint exists | by hand, see step 5 below |
| Reshare a tagged post or story to our story | no | by hand in the app |
| @mentions in other people's captions or comments | no (needs webhooks, not set up) | the tags list and DM story mentions cover most of it |

## Quick start
`PYTHONUTF8=1 python scripts/engage_daily.py` runs the whole read-only check for both accounts and writes
`engagement/reports/<date>.md` (not committed: it holds customer messages and signed story links). Claude drafts from that
report. After the day's items are handled run `engage.py tags-seen <acct>` so tomorrow's report only shows new tags.

## Every morning (about 09:00 IST). Claude runs it, Kainaat approves
1. **DMs.** `engage.py inbox <acct>` on both accounts. For each customer or creator whose message is last, show Kainaat
   (a) exactly what they sent (with the one or two messages before it) and (b) the reply Claude proposes. Numbered, so she can
   answer "approve 1 to 5, change 3 to ...".
   - A DM can only be sent within 24 hours of their last message. Older ones are shown as CLOSED: reply in a comment on their
     latest post, or in a story reply, instead of a DM.
   - Story mentions arrive in the inbox as `[mention]`. Reply in the DM and react on the story by hand.
2. **Comments on our posts.** `engage.py comments <acct>`. Every comment gets a reply within a day, never a generic emoji.
3. **Tags, collabs, mentions.** `engage.py tags <acct>`, plus the DM story mentions. For each: a comment on that post, and
   for partners and affiliates a collab ask (below).
4. **Other pages.** `engage.py watch-all <acct>` reads the newest post of every account in `engagement/targets.json`. Claude
   drafts a comment for each new post from the last 24 hours. Kainaat approves the list.
5. **Send what was approved.** DMs and comment replies on our own posts: `engage.py dm-send ... --send` and
   `engage.py reply ... --send`. Comments on OTHER accounts' posts: Instagram's API does not allow them, so Claude posts them
   in the signed-in browser (Kainaat signs in herself) or Kainaat pastes them in the app.
6. **Close the loop.** Mark handled items (`engage.py done`), log the day in `engagement/LOG.md` (counts, anything to follow up).

## Approval dashboard (added 20 Nov 2026)
Kainaat approves on a private page, "Engagement approvals" (an Artifact on her claude.ai account, its link is in chat, not in
this public repo). Each morning Claude writes the day's items into its `queue` collection with `ArtifactData`: the person's
exact words, our draft, the route (Instagram API, Chrome, or the app by hand). She edits, then Approves or Skips on the page.
Claude only sends items whose status is `approved`, then sets them to `sent` (or `byhand` when Instagram refuses). Pending
means nothing goes out.

## Approval rules
- Nothing goes out without her yes. A yes covers only the drafts she saw, with her edits.
- Never reply to anything that needs a decision (refund, price, medical question about a sick dog, legal, press): show it to
  her with a suggested answer and flag it.
- Dog health questions: warm, short, "please check with your vet", no claims, no dosing beyond what the product page says.
- No password, key, bank or card detail in any message, ever. Ask them to email care@theayurpet.com for anything private.

## Voice: witty, warm, ours
- A dog parent talking to a dog parent. Short. One joke at most, about the dog in THEIR post, never about us.
- Specific beats generic: name the dog, the thing in the photo, the move ("that sit is 90 percent negotiation").
- Plain words, no em dashes, no markdown, no hashtags in comments, at most two emojis, no "Great post!" or "Love this!!".
- Never sell in a comment. No links in comments. Never put a product claim in a joke.
- India account may use light Hinglish if the other person does. Global stays plain English.
- Examples: "Leo's walk face says he has already planned the second walk. 🐾" / "Zella is clearly the CEO here, we just work the
  snack desk." / "That nap has a better schedule than any of us."

## Partners and affiliates (the people who post about us)
Every time one posts, tags or mentions us:
1. Comment within the hour (the first hour counts most) in the voice above.
2. Thank them in a DM if it was a real feature, with one specific detail from their post.
3. Ask for the collab: "Would you add us as a collaborator on this post? It puts it on both our grids" (we send the invite;
   `ig.py collaborators <media_id>` shows the status). Reels and carousels only.
4. Ask for the right link: story link sticker or bio link pointing to their tracked affiliate link (from the affiliate
   program), plus @ayurpetofficial or @ayurpet_global tagged in the story. Send them the exact link, never ask them to type it.
5. Reshare to our story with their permission, tagging them.
Affiliates have a tracked link per person (see `ayurpet-affiliate`); the global account uses the .store link, India the .com link.

## Other pet content and brands (how we also engage)
Goal: be a regular, liked name in the places our dog parents already hang out. Target list: `engagement/targets.json`
(groups: partners, affiliates, creators, pet pages, brands). Claude keeps it growing: add 5 new accounts a week.
- **Creators and pet pages (mid-size, 5k to 300k):** comment within the first hour of their post, 2 or 3 a day, on their
  newest post only. Be the funny, specific comment, not the first one.
- **Brands (pet and non-pet, friendly ones):** a short witty reply, in the style of Ryanair or Duolingo, never a pitch.
- **Hashtag sweeps:** 2 a day on the recent tab (#dogsofindia, #indiedogs, #seniordogcare, #winterdogcare), 3 comments each on
  small accounts with under 20k followers. A real reply to someone's question beats a compliment.
- **Our own posts:** pin the best comment, answer every question, heart every comment, reply to the first 10 within the hour
  after posting.
- **Stories:** a question or quiz sticker twice a week; reshare every real mention within a day; reply to others' stories.
- **Collabs:** one collab invite or guest post idea a week with a creator or pet business (rescues, vets, trainers, groomers).
- **Moments:** festivals, dog days, viral formats: a quick on-brand post or comment while it is still trending.
- Follow back real dog accounts that engage. No follow/unfollow games, no engagement pods, no bought comments.

## Limits (so Instagram does not flag us)
- At most 20 comments a day per account on other accounts, spread through the day, none identical, none with links.
- At most 15 new DM conversations a day; replies to people who wrote first are not limited.
- Never comment on the same account more than 3 times a week unless they reply.
- If Instagram shows any warning or "try again later", stop for the day and tell Kainaat.

## Daily goal per account (comments on other accounts)
10 a day, spread through the day: 4 partners and affiliates, 2 pet pages, 2 influencers, 2 brands (set in
`engagement/targets.json`, `quota_per_account_per_day`). 20 is the hard cap above. After each one posted by hand run
`engage.py log-outbound <acct> --target <user> --permalink <url> --text "<comment>"`. It feeds the daily count and the
"we already commented" flag in `watch-all`. A target meant for India lists only `ayurpetofficial` in its accounts, so it is
never used from @ayurpet_global.

## Proposed schedule (waiting for Kainaat's yes)
09:00 IST: the morning check above, sent to her as a numbered list. 15:00 IST: a short second pass for new comments and DMs,
because the one-hour reply goal and the 24 h DM window need more than one look a day.

## Files
- `engagement/targets.json`: accounts to engage with (group, accounts, status, note). Stays on the laptop: this repo is
  public and the file names people who wrote to us. `engagement/targets.example.json` is a public-safe starter.
- `engagement/state.json`: handled DM and comment ids, tags seen, outbound comments logged. Not committed (same reason).
- `engagement/reports/`: the daily reports. Not committed.
- `engagement/LOG.md`: one line a day.
