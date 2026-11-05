# Posting and reading Instagram + Facebook without Zapier (since 5 Nov 2026)

Zapier's free tier ran out on 5 Nov 2026. Every AyurPet routine now talks to Meta's Graph API directly through
`scripts/ig.py` in this repo. It uses only Python's standard library, costs nothing and has no monthly cap.

## What was set up on Meta (5 Nov 2026)
| Piece | Value |
|---|---|
| Business portfolio | ayurpetofficial (935287898727459), verified |
| App | AyurPet Social Posting, id 29559569513660573, owned by the business |
| System user | Conversions API System User (61576681199350). Full access to The AyurPet page, @ayurpetofficial and @ayurpet_global; "Develop app" on the app |
| Token | system-user token, never expires. Second-admin approval by Karan on 5 Nov |
| Permissions | instagram_basic, instagram_content_publish, instagram_manage_comments, instagram_manage_insights, instagram_manage_messages, pages_show_list, pages_read_engagement, pages_manage_posts, pages_manage_engagement, pages_manage_metadata, pages_read_user_content, read_insights, business_management, ads_read |
| Not granted on purpose | ads_management (ads change only through the Meta ads connector, with Karan's OK), instagram_manage_contents (deleting posts) |

## Where the token lives
The token is never written into any repo, chat or log.
- **Karan's Mac:** `~/.config/ayurpet/meta_ig_token`, readable only by Karan's user.
- **Cloud routines:** the variable `META_IG_TOKEN` in the claude.ai/code environments "Default" (Reel Post, Carousel Post) and "AyurPet Reels" (Growth Analyst).
- **Kainaat's laptop:** Karan shares the token through a password manager. She sets it as the user environment variable `META_IG_TOKEN` (Windows: Settings, System, About, Advanced system settings, Environment Variables, New).

To replace the token: in Business Settings, go to System users, then Revoke tokens. Generate a new one (it needs a second admin's approval), then update all three places above.

## Commands
`python3 scripts/ig.py check` shows the permissions and both accounts' followers. Run `python3 scripts/ig.py -h` for the rest:
- **reel:** posts with collaborators, user tags and a cover.
- **carousel:** posts all slides in order.
- **story:** posts a story.
- **fb-photos:** posts several photos to the Facebook page.
- **media / insights / account-insights:** read posts and their numbers (views, reach, shares (sends), saves, watch time) and the account's new follows and unfollows.
- **collaborators:** shows a post's collab invite status.

Nothing goes live without `--publish`. Without it the tool only checks that Meta accepts and processes the post.

## Routines that use it
- AyurPet Reel Post: trig_01DJTJmosQWfCAfBvUgbfaUR
- AyurPet Carousel Post: trig_01Rrsn91T8VhbbT1rJUDmHhC
- AyurPet Reel Growth Analyst: trig_01QRgNXcDJV5PctKbApBPggw

If `META_IG_TOKEN` is missing, they post nothing and report FAILED.

The CEO Brief still names Zapier for its Instagram follower read. When that fails, it falls back to the Meta ads connector.
