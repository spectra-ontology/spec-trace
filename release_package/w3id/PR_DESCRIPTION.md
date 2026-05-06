# Register `/spectra` for the SPECTRA ontology

## Summary

Register `https://w3id.org/spectra` as the persistent IRI for **SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process**, an OWL 2 ontology for modeling the 3GPP RAN standardization document lifecycle (Tdoc, Resolution, CR, LS, Section, Spec, TechnicalReport, etc.).

## Affiliation and accountability

- **Institution**: System LSI Business, Device Solutions Division, Samsung Electronics, South Korea
- **Maintainers (with commitment to keep the redirect target alive)**:
  - Sihyeon Choi — shyun12.choi@samsung.com (corresponding maintainer)
  - Junho Lee — junho515.lee@samsung.com
- **Hosting**: GitHub release of [spectra-ontology/spec-trace](https://github.com/spectra-ontology/spec-trace) (v1.0.0 published, [release page](https://github.com/spectra-ontology/spec-trace/releases/tag/v1.0.0)); per-WG body-text knowledge graphs preserved on Zenodo (DOI [10.5281/zenodo.20034872](https://doi.org/10.5281/zenodo.20034872)).

## Why w3id

The SPECTRA ontology declares its IRI as `https://w3id.org/spectra#` so that the ontology and its terms remain dereferenceable across hosting changes. We commit to maintaining the GitHub repository and any future hosting moves through w3id redirects.

## Resource details

- **Type**: OWL 2 ontology (Turtle), 26 classes, 53 object properties, 81 data properties
- **License**: CC-BY 4.0
- **First public release**: v1.0.0 (2026-05-08)
- **Accompanying paper**: ISWC 2026 Resources Track (under review)

## .htaccess behavior

- `Accept: text/turtle | application/rdf+xml | application/n-triples` → latest GitHub release TTL ([example](https://github.com/spectra-ontology/spec-trace/releases/latest/download/spectra.ttl))
- Other / browser → PyLODE-rendered HTML on GitHub Pages ([https://spectra-ontology.github.io/spec-trace/](https://spectra-ontology.github.io/spec-trace/))
- Sub-paths (term IRIs like `/spectra#Tdoc`) → same TTL (single-file ontology)

## Files in this PR

- `spectra/.htaccess`

## Confirmation

- [x] I am authorized to register this IRI
- [x] The redirect targets are under our maintenance
- [x] The license (CC-BY 4.0) is explicitly stated in the released ontology
