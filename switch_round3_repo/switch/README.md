# Switch — local-data build with auth, ads, recommendations, and push groundwork

This is the six-original-screen "Switch" UX prototype (Home / My Courses /
Course Detail / Upload / Saved / Viewer), wired to the course-content
spreadsheet instead of a live Supabase project, with local file-backed auth
added on top. No external database, no network calls at runtime except the
YouTube iframe embeds themselves — everything else reads from JSON files
bundled in the repo.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

First run: you'll land on the sign-up/login screen (`pages/0_Auth.py`).
Sign up, pick your current semester from the real list the data has, and
you're in for up to 3 days without needing to log in again.

## What's here

**Local data layer (no external database).** `supabase_client.py`'s live
HTTP/RPC calls are replaced by `tree_store.py` (loads `data/tree.json`,
provides tree/search/grouping) and `local_client.py` (same function names
and shapes `supabase_client.py` had, so every page's import line was the
only required change versus the original prototype).

**Local auth (no external database, no plaintext passwords).** `local_auth.py`
— PBKDF2-HMAC-SHA256 with a random per-user salt; the raw password is never
written to disk. Session tokens (not passwords) persist across reloads via
`st.query_params`, file-backed in `data/sessions.json` with a 3-day expiry.
A valid session skips straight to Home with no re-prompt; an expired or
missing one routes to `pages/0_Auth.py`.

**Hierarchy-aware search.** `TreeStore.search()` tags node hits with which
tree level matched (faculty/department/course_unit/etc.) and link hits with
whether the query matched a title or a url, instead of one flat undifferentiated
list. `local_client.search_courses()` surfaces both to the search box.

**Per-topic grouping in Course Detail.** Every row in `repo_5.xlsx` ends its
path in the literal segment `"Class"`, so a course unit's 14+ links (for
Pathophysiology, for example) all share one tree node — see the caveat
below. `TreeStore.links_for_node_grouped()` splits them back into their real
topics (Epilepsy 2, Meningitis, Stroke, etc.) using each link's own `title`
field, and Course Detail renders a labeled section per topic instead of one
flat pile of cards.

**Red-coded inline YouTube embeds.** `tree_store.youtube_video_id()` extracts
the video id from a youtube url; `ui_components.youtube_embed()` renders an
actual playable iframe; `video_resource_card()` wraps that in a styled card
with a red (`#DC2626`) type chip. Reachable from Course Detail, Saved, Home's
search results, and the Viewer page.

**Per-user history and saved items.** `local_history.py` and `local_saved.py`
— file-backed, so a save or a "recently opened" entry survives a closed tab
within your 3-day session, not just the current browser tab.

## The data

`data/tree.json` was generated from `repo_5.xlsx` by `tools/import_content.py`.
Re-run it if the spreadsheet changes:

```bash
python tools/import_content.py path/to/repo_5.xlsx
```

Current import: **24 nodes, 157 links** (30 of them YouTube videos with
real, working urls).

### Two things worth knowing about the source data — not bugs, don't "fix" these

1. Every path in `repo_5.xlsx` ends in the literal segment `"Class"` rather
   than a per-topic name — this is why the title-based grouping above exists
   at all. The fix is at the link-grouping level (already built), not by
   trying to split `"Class"` into separate tree nodes.
2. The source file has two slightly different department-name spellings
   under Health Sciences (`"BMS   0000"` with extra internal spaces, and
   plain `"BMS"`) that produce two separate tree nodes rather than merging.
   This may reflect a real distinction in the source data — don't silently
   merge these.

## What's intentionally NOT here

- **Ads / "What's New on Campus" feed** — no ads table exists locally, so
  `fetch_feed()` returns empty and that section stays hidden.
- **Student uploads / crowdsourcing** — the Upload screen is still a
  placeholder form; content is added by re-running the importer.
- **Non-YouTube inline preview** — PDFs/slides/docs still show a placeholder
  box in the Viewer, not a real renderer; only YouTube gets a real embed.
- **A password-change or account-settings screen** — sign-out exists (top
  right of Home); nothing else account-related does yet.

## Project layout

```
app.py                  entry point — auth gate, routes to Home or sign-in
local_auth.py           local hash+salt auth, 3-day sessions (data/users.json,
                         data/sessions.json)
local_history.py        per-user "recently opened" (data/history.json)
local_saved.py          per-user saved/bookmarked items (data/saved.json)
ui_components.py        shared widgets — cards, tiles, nav, youtube embeds
local_client.py         drop-in for supabase_client.py — same functions,
                         backed by tree_store.py instead of HTTP
tree_store.py           loads data/tree.json, tree-walk + search + grouping
pages/
  0_Auth.py             sign-up / login
  1_Home.py             search, active-semester tiles, recent history, feed
  2_My_Courses.py
  3_Course_Detail.py    topic-grouped resources, video embeds
  4_Upload.py
  5_Saved.py
  6_Viewer.py           full-resource view, video embed, history recording
tools/
  import_content.py     xlsx -> data/tree.json converter
data/
  tree.json             generated — do not hand-edit; re-run the importer
  users.json, sessions.json, history.json, saved.json
                         generated at runtime as people sign up and use the
                         app — not checked in with real data
assets/manifest.json
.streamlit/config.toml
```


## Round 3 additions — ads, recommendations, and push groundwork

The existing student layout is preserved. The new work adds three capabilities
without replacing the current card/navigation system:

**Sponsored ads.** `local_ads.py` provides a local ad store, optional course-unit
targeting, active date windows, creative storage under `assets/ads/`, and basic
impression/click counters. Home renders eligible placements with the same `.card`
shell and labels them `SPONSORED`. The separate `pages/7_Admin.py` dashboard is
the authoring surface for advertisers/admins; students do not get an ad-upload
write path.

**Recommendations.** `local_recommendations.py` provides a provider-neutral
recommendation function using the user's existing durable history. Home adds a
`Recommended for you` section only when there is useful history. The returned
objects use the same resource shape as existing cards, so the current layout and
video rendering remain reusable.

**Push notification groundwork.** `local_notifications.py` stores
provider-neutral device subscriptions (iOS/Android/Web) and durable notification
jobs. The admin dashboard can queue a notification. It deliberately does not
pretend to send native push yet: a future cross-platform app can connect these
records to FCM, APNs, or Web Push without changing the admin/job contract.

### Admin access

`pages/7_Admin.py` is a separate dashboard. For this prototype set:

```bash
export SWITCH_ADMIN_USERNAME=admin
export SWITCH_ADMIN_PASSWORD=change-me
```

Windows PowerShell:

```powershell
$env:SWITCH_ADMIN_USERNAME="admin"
$env:SWITCH_ADMIN_PASSWORD="change-me"
```

Then open the Streamlit page for `pages/7_Admin.py`. In production, replace this
environment-variable gate with a real server-side admin role/identity system.

### Important snapshot limitation

The supplied Round 2 handoff document contains the source for the application
modules and explicitly describes `data/tree.json` as generated from `repo_5.xlsx`,
but it does not contain the actual 24-node/157-link JSON payload or the original
spreadsheet. Therefore this generated repository includes an empty `data/tree.json`
placeholder rather than inventing the missing course data. Restore the real
`repo_5.xlsx` and run `python tools/import_content.py path/to/repo_5.xlsx` before
expecting the course tree to populate.
