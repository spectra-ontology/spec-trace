# Publishing checklist (user actions)

> **STATUS: DRAFT — DO NOT EXECUTE until the ISWC 2026 paper is finalized.**
>
> The artifacts under `release_package/` (TTL, HTML docs, SHACL, queries,
> snippets, w3id PR template, Zenodo metadata, release notes) have been
> staged ahead of paper finalization. Steps below (GitHub release, Zenodo
> DOI mint, w3id PR submission, GitHub Pages activation) execute external
> services and are intentionally **not run yet** because:
>
> 1. The accompanying paper is still under revision; any change to author
>    list, version number, abstract, or contribution claims must be
>    reflected in `CITATION.cff`, `codemeta.json`, `.zenodo.json`,
>    `release_package/README.md`, and the w3id PR description before any
>    public artifact is created.
> 2. A Zenodo DOI minted from a tagged GitHub release is permanent — once
>    issued, the recorded title / authors / abstract cannot be silently
>    rewritten.
> 3. The w3id PR commits a long-lived redirect; the redirect target should
>    point at a release that is final.
>
> Only after the paper is finalized (camera-ready or final submission
> snapshot) and the metadata files are re-verified, run the steps below.

This checklist enumerates the manual steps required to turn the local
`release_package/` into a working, citable public release. The author has
assembled the artifacts below (with AI assistance for drafting and
consistency checks) including the metadata files (`CITATION.cff`,
`codemeta.json`); the steps in this file require account access that only
the human author has.

## 1. GitHub release (≈10 min)

The repository already exists at https://github.com/spectra-ontology/spec-trace.

```bash
# from repo root
git add release_package/
git commit -m "Add SPECTRA v1.0.0 public release package"
git push origin main

# Create a versioned release (uses GitHub CLI; install if needed)
gh release create v1.0.0 \
  --title "SPECTRA v1.0.0 — companion to ISWC 2026 submission (under review)" \
  --notes-file release_package/README.md \
  release_package/ontology/spectra.ttl \
  release_package/CITATION.cff \
  release_package/codemeta.json \
  release_package/LICENSE
```

After this, https://github.com/spectra-ontology/spec-trace/releases/tag/v1.0.0 will
exist and can be linked from the paper.

## 2. Zenodo DOI (≈10 min, one-time + per release)

Zenodo can mint a DOI for every GitHub release automatically once the
GitHub→Zenodo integration is enabled.

One-time setup:

1. Sign in to https://zenodo.org with your GitHub account.
2. Go to https://zenodo.org/account/settings/github/.
3. Toggle the `spectra-ontology/spec-trace` repository **on**.

Then, **re-run** the GitHub release step in §1 (or click "Edit" → "Save"
on the existing release). Zenodo will:

- archive the release tarball,
- mint a DOI of the form `10.5281/zenodo.<number>`,
- mint a *concept* DOI that always resolves to the latest version.

Both DOIs appear on the Zenodo project page within a few minutes.

## 3. Update the paper with the assigned DOI/URL

Once the DOI is assigned, edit two files:

- `docs/paper/iswc/latex/main.tex` (Resource Availability Statement, §8)
  - Replace `(DOI to be assigned upon acceptance)` with the actual DOI.
- `release_package/README.md`
  - Replace `[TODO: Zenodo DOI]` with the DOI.
  - Replace `[TODO: GitHub URL]` with the release URL (e.g. `https://github.com/spectra-ontology/spec-trace/releases/tag/v1.0.0`).

## 4. w3id.org redirect (REQUIRED — ontology IRI uses https://w3id.org/spectra)

The released ontology declares its IRI as `https://w3id.org/spectra#`. The
w3id redirect must be registered before the public release so that the IRI
resolves; without it the ontology IRI returns 404 and SPARQL endpoints
cannot dereference it.

Register the w3id redirect:

1. Fork https://github.com/perma-id/w3id.org.
2. Add a `spectra/` directory containing an `.htaccess` file:

   ```apacheconf
   # /spectra/.htaccess
   Options +FollowSymLinks
   RewriteEngine on
   RewriteRule ^$  https://github.com/spectra-ontology/spec-trace/releases/latest [R=302,L]
   RewriteRule ^(.*)$  https://github.com/spectra-ontology/spec-trace/releases/latest/download/spectra.ttl [R=302,L]
   ```

3. Submit a PR. Acceptance is usually within a few days.

After the PR is merged, `https://w3id.org/spectra` resolves to the latest
GitHub release; loading the ontology by its declared IRI works from any
Semantic Web tool.

## 5. Verification

After publication, verify:

- [ ] `https://doi.org/<your-doi>` resolves to the Zenodo record.
- [ ] The Zenodo record lists `spectra.ttl` as a downloadable file.
- [ ] The GitHub release v1.0.0 page is publicly viewable.
- [ ] `CITATION.cff` is detected by GitHub (the "Cite this repository" button appears).
- [ ] The license badge shows CC-BY-4.0.
