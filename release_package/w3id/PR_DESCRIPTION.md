# Register `/spectra` for the SPECTRA ontology

## Summary

Register `https://w3id.org/spectra` as the persistent IRI for **SPECTRA: A Traceability Ontology for the 3GPP RAN Standardization Process**, an OWL 2 ontology for modeling the 3GPP RAN standardization document lifecycle (Tdoc, Resolution, CR, LS, Section, Spec, TechnicalReport, etc.).

## Affiliation and accountability

- **Institution**: Samsung System LSI, South Korea
- **Maintainers (with commitment to keep the redirect target alive)**:
  - Sihyeon Choi — shyun12.choi@samsung.com (corresponding maintainer)
  - Junho Lee — junho515.lee@samsung.com
  - Joon-Hyoung Ahn — junyung.ahn@samsung.com
- **Hosting**: GitHub release of [spectra-ontology/spec-trace](https://github.com/spectra-ontology/spec-trace), preserved on Zenodo (DOI to be minted upon GitHub release).

## Why w3id

The SPECTRA ontology declares its IRI as `https://w3id.org/spectra#` so that the ontology and its terms remain dereferenceable across hosting changes. We commit to maintaining the GitHub repository and any future hosting moves through w3id redirects.

## Resource details

- **Type**: OWL 2 ontology (Turtle), 26 classes, 53 object properties, 81 data properties
- **License**: CC-BY 4.0
- **First public release**: v6.1.1 (2026-04-27)
- **Accompanying paper**: ISWC 2026 Resources Track (under review)

## .htaccess behavior

- `Accept: text/turtle | application/rdf+xml | application/n-triples` → latest GitHub release TTL
- Other / browser → latest GitHub release page (HTML PyLODE doc accessible from the release assets)

## Files in this PR

- `spectra/.htaccess`

## Confirmation

- [x] I am authorized to register this IRI
- [x] The redirect targets are under our maintenance
- [x] The license (CC-BY 4.0) is explicitly stated in the released ontology
