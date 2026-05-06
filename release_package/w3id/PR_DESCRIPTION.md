<!-- Recommended W3ID Pull Request Details. -->
## Brief Description

This PR adds a new persistent identifier directory `/spectra` for **SPECTRA — A Traceability Ontology for the 3GPP RAN Standardization Process** (companion to an ISWC 2026 Resources Track submission, currently under review). The directory contains only redirect configuration with content negotiation: `text/turtle` (and equivalent RDF serialisation Accept headers) → ontology TTL on GitHub releases; HTML/browser → PyLODE documentation on GitHub Pages.

Requested namespace:

```text
https://w3id.org/spectra#
```

Ontology document IRI:

```text
https://w3id.org/spectra
```

Redirect targets (all verified HTTP 200 prior to this PR):

- HTML / browser → [https://spectra-ontology.github.io/spec-trace/](https://spectra-ontology.github.io/spec-trace/)
- `text/turtle`, `application/rdf+xml`, `application/n-triples` → [https://github.com/spectra-ontology/spec-trace/releases/latest/download/spectra.ttl](https://github.com/spectra-ontology/spec-trace/releases/latest/download/spectra.ttl)
- Sub-paths (term IRIs like `/spectra#Tdoc`) → same TTL (single-file ontology)

The ontology content and documentation are hosted externally in the GitHub repository [spectra-ontology/spec-trace](https://github.com/spectra-ontology/spec-trace) (v1.0.0 published, [release page](https://github.com/spectra-ontology/spec-trace/releases/tag/v1.0.0)); the per-WG body-text knowledge graphs are deposited on Zenodo (DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872)).

## General Checklist

- [x] Changes have been tested. (TTL latest-download: HTTP 200; GitHub Pages root: HTTP 200; both verified.)
- [x] The number of commits is minimal. Squash if needed.
- [x] Commits only include redirects and basic information. Serving content and full documentation is not supported on this service.

## New ID Directory Checklist

- [x] Maintainer details are in `.htaccess`.
- [x] GitHub username ids are listed in the maintainer details.

## Resource details

- **Type**: OWL 2 ontology (Turtle), 26 classes, 53 object properties, 81 data properties
- **License**: CC-BY 4.0 (SPECTRA-authored components); per-WG body-text literals on Zenodo retain explicit 3GPP attribution
- **Maintainers**:
  - [@shychoi10](https://github.com/shychoi10) — Sihyeon Choi (corresponding) — shyun12.choi@samsung.com
  - Junho Lee — junho515.lee@samsung.com
- **Affiliation**: System LSI Business, Device Solutions Division, Samsung Electronics, South Korea
- **Files in this PR**: `spectra/.htaccess`

## Optional Requests for W3ID Maintainers

- [x] Please squash commits for me.
