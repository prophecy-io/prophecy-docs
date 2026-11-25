# Curation rules — public change log

Every run must read this file and apply these rules before drafting. These are
standing exclusions on top of the base spec (which already drops internal
refactors, tests, CI/CD, infra, dependency bumps, and no-impact changes).

Each rule records the review comment it came from. When a new standing rule
is added, keep the structure: rule, **Why**, **How to apply**, dated example.

> TODO(D): fill in the lines marked `TODO(D)` before the first run, then
> delete this note and the markers.

## Hard exclusions (never publish)

- **GA-only — include an item ONLY if the source confirms it is generally available.**
  Default to exclude. An item qualifies only when the source confirms either no
  gating feature flag, or that the gating flag is effectively on for everyone in
  EVERY production environment (accounting for the On/Off switch, not just the
  fallthrough). On in one environment and off in another is NOT GA. If an item
  is behind a flag that defaults off (or to targeted beta), or GA can't be
  confirmed, leave it out — do not soften or hedge. "Merged to main" is not
  enough. Ask the source, per change, for: gating flag name (if any), its
  state per environment, and a yes/no on GA.

- **MCP server: publish only what the docs cover.** Prophecy documents its MCP
  server only for connecting a Microsoft Copilot Studio agent. Publish an MCP
  server item only when it changes something a Copilot Studio user would
  notice, and link the Copilot Studio page. Hold everything else about the MCP
  server (other AI clients, new connection methods, undocumented tools or
  auth flows): those go on the held-items watchlist with `engineering-gated` in
  their notes, and release only when engineering confirms them and the docs
  cover them, not on a flag flip.
  **Why:** the change log must not announce a capability the docs don't cover.
  (In the rule set this was ported from, several MCP server and public API
  items were pulled after or just before publishing.)
  **How to apply:** the test is whether the item describes the MCP server, not
  whether a word like "MCP" appears. If it's unclear whether an item affects
  Copilot Studio users, hold it and ask in the PR body's ruling requests.

- **No implementation-detail items.** The change log describes user outcomes,
  not plumbing. Exclude items whose substance is an endpoint's filter/sort
  parameters, delivery mechanics, or other technical implementation details —
  even when GA. These are permanent editorial exclusions — they do NOT go on
  the held-items watchlist.

- **Pre-launch fixes and polish are part of the launch.** When a feature
  reaches GA in the covered period, work that fixed or polished it BEFORE
  customers could see it is not a separate bug fix or improvement — customers
  never experienced the broken state. Fold it into the launch item or drop
  it. Only list a fix separately if the broken behavior was live for customers.

## Voice and framing

- **Lead features with user value, not UI rework.** A launch bullet should
  say what the feature does for the user, not "redesigned editor and list."
- **Don't present existing capabilities as new.** If a change increases how
  often or how well an existing behavior shows up, describe it as that — not
  as a new capability.

## GA carve-outs (narrow segment exceptions don't block publishing)

A flag counts as GA if its fallthrough/default serves `true` to everyone, even
if a narrow named-segment rule still serves `false` to a specific account or org
(e.g. one enterprise customer opted out). Publish the item; don't hold it for a
single-account carve-out. Only hold items where the *fallthrough itself* is off
or targeted-beta.

## Flag-flip watchlist (re-check previously-held items)

Every item dropped as non-GA must be logged to `held-items.json` (open
watchlist), not silently discarded. Each run, before the normal commit-diff
query, re-check every open watchlist item's flag against its CURRENT state.
If a flag has flipped to on everywhere, the item is "recovered": publish it
dated to the FLIP date (when it became visible to users), not its original
merge date, then move it from the open watchlist to the resolved log.

**Why:** the workflow dedups on `cutoff_sha` — a git commit diff. A flag flip
is not a commit. A feature that merged, was correctly held (flag off), and then
flipped on a week later would never be asked about again, because its SHA is
already behind the cutoff. This was only caught because someone noticed the
feature live in the product.

**How to apply:** treat "excluded for not-GA" as a pending state, not a
terminal one. The watchlist keeps pending items in front of us until the flag
system confirms GA.

## Tags — canonical vocabulary

Exactly three tags, matching the `###` subsections an entry actually contains,
written exactly as the subsection names. Never invent one, never use cadence
labels like "Weekly update".

| Subsection heading | Tag in `tags={[...]}` |
| ------------------ | --------------------- |
| New features       | `"New features"`      |
| Improvements       | `"Improvements"`      |
| Bug fixes          | `"Bug fixes"`         |

The vocabulary lives in three places that must agree:

1. each `<Update>` block's `tags` attribute
2. `SUBSECTIONS` in `mintlify_entry.py`, which exists twice and must stay
   identical: in the skill's `scripts/` and in this repo's `.changelog/` (used by CI)
3. this file

**Why:** readers filter the change log by these values. A second spelling
splits entries across two filters, and an entry carrying an unknown tag drops
out of the filter its readers expect.

**How to apply:** derive tags mechanically from the subsections present. If a
tag would fall outside the three above, the entry is structured wrong — fix the
structure, not the tag.

## Links

Links to docs pages are root-relative, with no file extension:

    [Pull from Remote](/section/page)

Full `https://` URLs are fine for pages outside the docs site.

**Why:** Mintlify resolves root-relative links from the site root, so they keep
working if the docs domain changes. Relative paths (`../page`) and `.mdx`
extensions break depending on where the change log page sits.

**How to apply:** never emit a relative path or an `.mdx` link from a change
log entry. Verify a target resolves on the live docs site before linking it.
(The change log has no RSS feed. If one is added, switch to full URLs, since
root-relative links don't resolve in feed readers.)

## Terminology

Current product names. Earlier terms are correct only when describing history.

`TODO(D): add the remaining current names and the old names still in code,
commits, and flag names.`

| Use | Not |
| --- | --- |
| DataGPT | dataGPT, DGPT |
| the Agent | [old names still in code or flags] |

**Why:** products get renamed, and the source data (commits, flag names, code)
still carries older names. An entry announcing a feature under a name the UI no
longer uses sends readers looking for something that isn't there.

**How to apply:** translate source terminology before drafting. If an item's
name is ambiguous, describe the surface the user actually sees.

## Output format

**File:** the change log page at `changelog_path` in `.changelog/state.json`.

**Never modify:**

- The page's frontmatter (`title`, `description`, and anything else in it).
- Anything above the `{/* changelog-entries */}` marker line, including the
  marker itself.
- Existing entries below the marker.
- `docs.json` or any other page. Navigation lives in `docs.json`, and the
  change log job never touches it.

**Only add:** one new `<Update>` block directly below the marker, so the newest
entry is first.

Entry shape:

    <Update label="YYYY-MM-DD" tags={["New features", "Improvements", "Bug fixes"]}>

    ## Short headline naming the most significant change

    One sentence summarizing the release.

    ### New features

    * **Feature name** — What it does and why it matters.

    ### Improvements

    * **Short label** — What changed.

    ### Bug fixes

    * **Short label** — What was fixed.

    </Update>

- `label` is the covered week's Sunday as `YYYY-MM-DD`. It renders beside the
  entry and identifies the week; the job checks it to avoid publishing a week twice.
- The opening tag stays on one line, and `</Update>` is the last line.
- The `##` heading is a **headline, never a date**. The date already displays
  from `label`, and this heading populates the on-page navigation.
- `###` subsections are limited to New features, Improvements, Bug fixes. Omit
  any with no content.
- Bullets use `* **Bold label** — description.`
- The page is MDX: curly braces and literal tags (`{}`, `<Foo>`) go inside
  backticks, or the page fails to build.

**Why:** the page header belongs to the docs team and the entries belong to
this pipeline, in the same file. The marker is the boundary between them.

**How to apply:** treat everything above the marker as read-only.

## Enforcement

`scripts/mintlify_entry.py` checks each draft before anything is pushed, and
`push-changelog.sh` refuses changes to any file outside the allowlist. CI
(`.github/workflows/validate-changelog.yml`) runs on every PR and in the merge
queue, and fails when:

- `state.json` or `held-items.json` is invalid, or `state.json` lacks
  `last_entry_date`, `cutoff_sha`, or `changelog_path`.
- The marker is missing or repeated, or anything other than `<Update>` blocks
  follows it.
- Any entry fails the entry check (tags, headline, subsections, links,
  MDX-breaking characters), its label isn't a Sunday, labels repeat, or
  entries aren't newest first.
- A `changelog/*` branch changes a file outside the allowlist, edits anything
  above the marker, or changes an existing entry instead of adding one.
- The page fails to compile as MDX. This matters while the page is in
  `.mintignore`, because Mintlify doesn't build it then.

People can still fix typos in past entries on their own branches; only
`changelog/*` branches are limited to adding one entry.

**How to apply:** if the check fails, fix the entry rather than the check.

## Sourcing and authority

- **One source of record per run.** The weekly commit list, every GA
  determination, and the end-of-week cutoff SHA come from one source: either
  the runner reads the product repo and flag system directly (`self` mode), or
  it asks a source agent in the source channel (`delegate` mode). Never infer GA
  from the product UI, commit messages, or memory, and never mix modes in one
  run. No answer from the source = no entry and no state change.
  **Why:** a guessed GA call publishes features customers can't see.
  **How to apply:** in `self` mode post ONE evidence message in the source
  channel (watchlist results and the diff table) before drafting, and link it
  from the PR body. In `delegate` mode, if the source doesn't answer within the
  polling window, post the no-response notice and stop without advancing state.

- **Curation subtracts; it never adds.** These rules may exclude or hold items
  the source reported — including overriding a GA-yes by engineering ruling —
  but may never add or promote an item the source didn't confirm.

- **The product repo's production branch is `origin/main`.** Never a dev branch.
  **Why:** diffing the wrong branch reports unshipped work.

- **Diff window and cutoff discipline.** Covered week = the most recent
  complete Mon–Sun. Window = state.json `cutoff_sha` → last Sunday 23:59:59
  local time. The new cutoff is main's SHA at that instant — NOT current HEAD.
  The cutoff advances only when the week's output is actually delivered; every
  failure path stops without advancing state.
  **Why:** commits after Sunday belong to next week; advancing state on a
  failed run silently drops a week.
  **How to apply:** use the correct UTC offset for that Sunday (DST changes).

- **Cadence.** Mondays at 10:00 UTC (02:00 or 03:00 in `CHANGELOG_TZ`, after
  the week closes), covering the prior Mon–Sun. No-change weeks still run: open
  a PR that advances only the `.changelog/` state, and post the one-line
  notice. Never duplicate a week already on the change log page.

## Publishing pipeline

- **Terminology:** the deliverable is the "change log" — that wording in PR
  titles, commit messages, PR bodies, and Slack.

- **Target and format.** The change log page in the docs repo, per **Output
  format** above. New blocks insert immediately below the marker line (newest
  first); `label` is the covered week's END date (the Sunday). Recovered
  watchlist items go in that same entry; their flip date goes in the PR body's
  Recovered line, since one run publishes one entry.

- **The reviewer's PR merge is the only publish gate.** Never merge a PR; never
  push to `main`. `main` is protected and merges go through the merge queue;
  Mintlify deploys the docs site from `main`, so merge = publish. No-change
  weeks also go through a PR, which touches only `.changelog/` files and
  publishes nothing.

- **File allowlist.** Only the change log page and `.changelog/*` may be
  modified. Never `docs.json`, other pages, snippets, or workflows.

- **Open-PR guard.** If a `changelog/*` PR is still open, the prior week is
  unreviewed: notify the review channel (no mentions), skip the run, and let the
  unadvanced cutoff fold the week forward. One PR in flight at a time.

- **GitHub writes go through the skill's push script only.** No ad hoc git or
  API writes; never work around a guard; never edit the script mid-run.

- **Branch/PR conventions and evidence chain.** Branch
  `changelog/{week-start}-to-{week-end}`; commit "docs: change log — week of
  {range}". PR body carries: counts by category, the cutoff line (old → new
  SHA), the Held list, the Recovered list, reviewer-ruling requests, and the
  evidence chain. After pushing, re-read the change log page on the branch and
  confirm the new entry is present and nothing was lost.

- **State files are the source of truth in the repo.** `.changelog/state.json`,
  `held-items.json`, and this file. Read them from the repo each run, not from
  local copies.

- **Notifications.** Nobody is tagged in the review channel except the operator
  in a failure alert; the only mentions anywhere are the source agent in the
  source channel (`delegate` mode only) and the operator in a failure alert.
  Blocked or failed runs post nothing else to Slack.

- **Feedback loop.** The reviewer's PR feedback is applied as commits to the
  same `changelog/*` branch. When feedback establishes a new standing rule,
  append it to this file in the same commit. Until `push-changelog.sh` has a
  feedback mode, the runner replies in the review thread with the exact
  revised text and pushes nothing; the reviewer applies it.

## Additional voice rules

- **Security fixes: calm, factual language.** No alarming language, no urgency,
  no implication of customer exposure. Severity context belongs in the PR body.
  **Why:** alarmed wording reads as an incident disclosure.

- **House voice.** Plain, direct, factual; no hype, no speed claims, no emojis,
  no hashtags. Follow the Prophecy docs style:
  - Active voice and second person ("You can now...").
  - "Prophecy creates" / "Prophecy copies" for what the system does.
  - Bold UI element names; leave action verbs plain.
  - Precise product terms (e.g. "Historical Mode", "conditional gem"), per
    **Terminology** above.
  - User tasks and behavior, not implementation details.
  - Every bullet ends with a period, even a fragment.

- **No surface tags.** Every change currently lands in the Prophecy web app, so
  bullets carry no "(Surface)" suffix. If an item lands somewhere else, ask
  the reviewer in the PR body how to label it.

- **The Agent by name, never "she"/"he".** Prophecy's in-product AI assistant is
  "the Agent", capitalized. Use the name or restructure the sentence; "it" only
  as a last resort. Use "they" for people.

- **Attribute changes to their exact surface.** Name the specific feature area
  the change applies to — don't describe it generically as "chat" or "agents."

- **Display-only permission fixes must say so.** When a fix hides a control the
  user could see but not use (the behavior was already permission-gated), frame
  it as a display-only fix so it can't be read as closing a security gap.

- **Lead the bug-fix list with the fix customers feel most.** Not commit order,
  severity label, or surface. Same for the `##` headline and summary sentence.

- **A removed code gate is not an availability claim.** Removing a flag, tier
  check, or entitlement gate changes how code is gated; it is not evidence that
  packaging or entitlements changed. Never write "now available to everyone"
  from a diff without explicit confirmation from the reviewer.
  **Why:** availability claims are the ones customers act on and sales gets
  asked about; a wrong one is worse than an omission.

- **Hardening and internal-mechanism items get dropped, not reworded.** If a
  change can't be stated as an outcome the reader would recognize, leave it out.
  Permanent editorial exclusion, not watchlisted.
  **How to apply:** draft the bullet, then ask what a customer would do
  differently knowing it. If there's no answer, cut it.

## Review notifications

- **The review post is one short message with no mentions:**
  `**docs: change log — week of {range}** {PR URL} — Ready for review. Merging the PR publishes to the docs site.`
  No change list or counts; all detail lives in the PR body. The docs team
  requests reviewers when it picks up the PR; the runner never does.
  **Why:** a long Slack digest duplicates the PR body and gets skipped.

## Fold-forward weeks are merged, not stacked

When a run is skipped and `cutoff_sha` does not advance, the next successful
run covers more than one week. Publish that as **one** entry, dated to the
later week's end date — not one block per week stacked on top of each other.
**Why:** two adjacent blocks from one PR read as one item split in half.

## Notes

- Exclusions apply to the public change log only — they do not change what the
  source reports internally.
