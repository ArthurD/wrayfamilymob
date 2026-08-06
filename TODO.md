# TODO

Running list for wrayfamilymob.com. Newest decisions at the top of each section.

## Decisions on record

- **Repo stays public for now.** Public keeps the project auditable, traceable,
  and fact-driven — every change is attributable and externally verifiable.
  Switching to private is on the list below, not off the table.

## Deferred

- [ ] **Make the GitHub repo private.** Deferred deliberately; public is
      preferred while the project is being assembled. Revisit once the character
      set and photo library are settled. Note that going private later does not
      retract anything already cloned or cached, so this is a change of posture
      rather than a rollback.
- [ ] **Decide the removal path.** The current architecture — public repo, git
      history, CDN caching, airgapped mirror — is built for durability, which
      makes taking something down correspondingly hard. If any subject asks to be
      removed, honoring it means a history rewrite, force-push, mirror purge, and
      CDN purge, and it will not reach existing clones. Worth settling the
      procedure while the set is small.

## Blocked — need a Full Access Spaces key

The current key is Limited Access (objects only). These three all fail with
`AccessDenied` until a Full Access key exists; a Personal Access Token cannot
substitute, as bucket config goes through the S3 API, not DO's REST API.

- [ ] **Object versioning** on `wray-family`. One-way — once enabled it can only
      be suspended, never removed. Confirm before enabling.
- [ ] **Access logging** → `wray-logs-sfo2`, prefix `wray-family/`. Target bucket
      is in sfo2, matching the source, which is required. The older `wray-logs`
      in sfo3 cannot be used.
- [ ] **Static website index document.** Would fix the 403 on the bare `/` path.
      Note this may not help the custom domain even once set — index-document
      routing appears to apply to the `-static` endpoint rather than through the
      CDN. Needs an empirical test once the key exists.

## Content

- [ ] **Merge the book's `characters.json`** against the six existing entries.
      Watch for slug collisions and alternate spellings of the four Wray names.
- [ ] **Identify the 15 photos in `pending-review/`** and wire them into
      `photos.json` with the right `people` lists.
- [ ] **Write `summary` and `role`** for each character from the book.
- [ ] **Decide the default carousel slide.** Slide one is currently the annotated
      version, which has `Kailyn Wray (now 16yr old, niece)` burned into the
      image. The unlabelled version of the same photo is slide two. One-line
      reorder in `links.json`.

## Site and infrastructure

- [ ] **Apex domain.** `wrayfamilymob.com` does not resolve — only
      `www.wrayfamilymob.com`. DNS forbids a CNAME at the zone apex and DO has no
      ALIAS record. Fixing it means moving DNS to a provider with CNAME
      flattening, e.g. Cloudflare.
- [ ] **Lower the CDN edge TTL** from 1 hour to ~1 minute while iterating.
      Deploys currently take up to an hour to appear on the custom domain.
- [ ] **Delete the stray DNS record**
      `wray-family.sfo2.cdn.digitaloceanspaces.com.wrayfamilymob.com` — created
      by pasting the CDN endpoint into the hostname field. Inert but confusing.
- [ ] **Install `python-magic`** so s3cmd stops guessing MIME types by extension.

## Security cleanup

- [ ] **Delete orphaned Spaces keys** in the DO panel. Several stray secrets were
      generated while sorting out the key pair; only the working one is needed.
- [ ] **Delete the local `backup-pre-scrub` branch.** It still contains the old
      `.s3cfg` with the retired secret in its history. Local only — never push it.
      `git branch -D backup-pre-scrub`
- [ ] **Untrack `site/index.html` and `.claude/settings.local.json`.** Both are
      listed in `.gitignore` but were committed before it existed, so they remain
      tracked. `site/index.html` is generated output and dirties the tree on every
      build.

## Done

- [x] Domain delegated to DO nameservers; `www` CNAME → CDN endpoint; wildcard
      Let's Encrypt cert issued.
- [x] Site live at `https://www.wrayfamilymob.com/index.html`.
- [x] `build.py` / `deploy.sh` pipeline, JSON-driven.
- [x] Home-page carousel with arrow, dot, and keyboard navigation.
- [x] Many-to-many photo↔person model (`photos.json`), plus per-person folder
      shortcut at `materials/photos/people/<slug>/`.
- [x] Old Spaces key rotated and deleted; secret purged from git history before
      it ever reached GitHub.
- [x] Shipping label with a third party's home address moved to `withheld/`
      (gitignored, kept not deleted).
