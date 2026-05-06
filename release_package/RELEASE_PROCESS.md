# Release Process — SPECTRA v1.0.0

**Status (2026-05-06)**: All release steps below have been **completed**. This document is retained as the historical record of the v1.0.0 release process and as a template for future releases.

| Step | Status | Result |
|---|---|---|
| GitHub push to `spectra-ontology/spec-trace` | ✅ Completed | https://github.com/spectra-ontology/spec-trace |
| GitHub Pages activation (`main`/`docs`) | ✅ Completed | https://spectra-ontology.github.io/spec-trace/ |
| GitHub Release v1.0.0 | ✅ Completed | https://github.com/spectra-ontology/spec-trace/releases/tag/v1.0.0 |
| Zenodo deposit publish | ✅ Completed | DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872) (minted 2026-05-08) |
| w3id PR submission | ✅ Submitted | [perma-id/w3id.org#6021](https://github.com/perma-id/w3id.org/pull/6021) (in review) |

The detailed step-by-step record below documents the actions taken and reasoning, useful as a reference for subsequent releases or for reviewers wanting to understand the release process.

---

## Process Record

This document originally enumerated the manual steps required to make the SPECTRA
v1.0.0 release publicly resolvable for the ISWC 2026 Resource Track
submission. All artifact-side preparation was staged in the local
repository; the steps below required account access only the human author
had (GitHub push, Zenodo upload + publish, w3id PR submission). All steps are now complete (see status table above).

## Architecture: GitHub + Zenodo split

Because four of the five per-WG body-text TTLs exceed GitHub's 100 MB
per-file limit (RAN1 185 MB, RAN2 186 MB, RAN4 279 MB, RAN5 186 MB), the
v1.0.0 release is distributed across two channels:

| Channel | Contents | Why |
|---|---|---|
| GitHub repository | ontology, SHACL, SpectraCQ, schema-instantiation TTLs (~14 KB each), validation, scripts, supplement, pipeline | small, free, easy to clone, supports `verify_release.py` |
| Zenodo deposit | per-WG body-text TTLs (~922 MB total), full mirror archive of GitHub | per-record 50 GB capacity, persistent DOI, IPR-attributed |

The local `.gitignore` excludes `release_package/kg/per_wg/*.ttl` so the
GitHub push will not attempt to upload the large body files.

## Day-by-day timeline (Mon 2026-05-04 → Fri 2026-05-08)

### Day 2 — Tue 2026-05-05: GitHub push + w3id PR (≈1 h, fully reversible)

1. Commit the staged release artifacts and push to the public mirror:
   ```bash
   bash scripts/paper/sync_to_public.sh
   ```
   The sync script copies `release_package/` to a clean checkout of the
   public mirror, commits, and pushes. Body TTLs are excluded by
   `.gitignore`.

2. Verify the public state:
   ```bash
   curl -I https://raw.githubusercontent.com/spectra-ontology/spec-trace/main/release_package/README.md
   curl -I https://raw.githubusercontent.com/spectra-ontology/spec-trace/main/release_package/kg/per_wg_schema/RAN1-schema.ttl
   ```
   Expected: HTTP 200 for both. (`kg/per_wg/RAN1-body.ttl` will be 404 by
   design.)

3. Submit the w3id PR (template ready at `release_package/w3id/`):
   - Fork https://github.com/perma-id/w3id.org under your GitHub account.
   - Create `spectra/.htaccess` with the contents of
     `release_package/w3id/htaccess`.
   - Open a PR against `perma-id/w3id.org:master` using
     `release_package/w3id/PR_DESCRIPTION.md` as the PR body.
   - PR review usually takes 3–7 days; once merged,
     `https://w3id.org/spectra` redirects to the GitHub release page.

4. (Optional but recommended) Enable the GitHub-Zenodo integration:
   - Sign in to https://zenodo.org with your GitHub account.
   - Toggle `spectra-ontology/spec-trace` ON at
     https://zenodo.org/account/settings/github/.
   This lets a future GitHub release auto-archive on Zenodo for the
   small-file mirror; the body TTL deposit is uploaded manually
   (next day).

### Day 3 — Wed 2026-05-06: Zenodo deposit (≈1.5 h; mint = irreversible)

1. Create a new Zenodo deposit at https://zenodo.org/uploads/new.
   Import metadata from `.zenodo.json` (Zenodo accepts the Upload-tab
   "Import" feature, or copy fields manually).

2. Upload the five per-WG body TTL files from
   `release_package/kg/per_wg/`:
   - RAN1-body.ttl (185 MB)
   - RAN2-body.ttl (186 MB)
   - RAN3-body.ttl (85 MB)
   - RAN4-body.ttl (279 MB)
   - RAN5-body.ttl (186 MB)
   Estimated upload: 30–60 minutes on a typical residential link.

3. Reserve a DOI ("Save draft" auto-reserves a DOI; the deposit is still
   editable until you click Publish).

4. Edit the paper RAS to use the reserved DOI (replace the
   `10.5281/zenodo.20034872` placeholders in `docs/paper/iswc/latex/main.tex`
   and `release_package/README.md`).

5. Recompile the paper PDF and run `verify_release.py` once more.

6. **Publish** the Zenodo deposit. **This is irreversible** — the DOI is
   permanent; metadata can only be amended via Zenodo's "edit metadata"
   feature, and files can only be replaced by issuing a new version.

### Day 4 — Thu 2026-05-07: Final verification + buffer

1. Verify the published DOI URL resolves and lists all five TTL files.
2. Verify the GitHub repository is in sync with the local `release_package/`.
3. Verify the paper PDF MD5 matches the desktop copy.
4. Pre-fill EasyChair submission metadata.

### Day 5 — Fri 2026-05-08: Submission

Upload the final PDF to EasyChair before 23:59 AoE.

## Post-acceptance (camera-ready, typically ~2 months later)

- Update the GitHub README badge with the live Zenodo DOI image.
- Replace any "(under review)" wording.
- If the paper title/authors change, issue a Zenodo new-version mint with
  corrected metadata (the original DOI remains as v1, the new DOI v2).

## Verification commands (copy-paste)

```bash
# Local artifact integrity (run before push):
python3 release_package/tests/verify_release.py
# Expected: 37/37 PASS (all checks).

# Public reachability after push (run after Day 2):
curl -ILs https://github.com/spectra-ontology/spec-trace                | head -1
curl -ILs https://w3id.org/spectra                                      | head -1
curl -ILs https://doi.org/10.5281/zenodo.20034872                        | head -1
```
