# SPECTRA Schema Overview

A textual/ASCII summary of the ontology structure. A polished figure version
will be shipped separately as part of the camera-ready paper release.

## Class hierarchy (top-level groupings)

```
Tdoc  (the primary contribution unit)
├── CR            (Change Request)
├── LS            (Liaison Statement)
├── Summary
└── SessionNotes

Resolution  (meeting outcomes)
├── Agreement
├── Conclusion
└── WorkingAssumption

Spec        (Technical Specifications)
Section     (hierarchical sections inside Specs)
TSTable     (tables inside TS sections)
TSFigure    (figures inside TS sections)
TechnicalReport
TRImpact    (link between a TR and a Spec it affects)
CRPack      (packaging of related CRs)

Meeting
WorkingGroup
WorkItem
AgendaItem
Release

Company     ⊑ foaf:Organization
Contact     ⊑ foaf:Person

Figure, Table, Chart  (generic artefacts used in Tdocs)
```

## Key relationships

- `Tdoc -[:presentedAt]-> Meeting`
- `Tdoc -[:submittedBy]-> Company`
- `Tdoc -[:relatedTo]-> WorkItem`
- `Resolution -[:madeAt]-> Meeting`
- `Resolution -[:references]-> Tdoc`  (Resolution cites a contributing TDoc)
- `Resolution -[:resolutionBelongsTo]-> AgendaItem`
- `CR -[:modifies]-> Spec`, `CR -[:modifiesSection]-> Section`
- `CR -[:belongsToCRPack]-> CRPack`
- `CRPack -[:hasCR]-> CR`  (`owl:InverseFunctionalProperty`)
- `Section -[:hasSubSection]-> Section`  (`owl:IrreflexiveProperty`, `owl:AsymmetricProperty`)
- `Section -[:parentSection]-> Section`
- `Section -[:belongsToSpec]-> Spec`
- `TRImpact -[:impactOfTR]-> TechnicalReport`, `TRImpact -[:impactsSpec]-> Spec`
- `TechnicalReport -[:hasTRImpact]-> TRImpact`  (`owl:InverseFunctionalProperty`)
- `LS -[:sentTo]-> WorkingGroup`, `LS -[:originatedFrom]-> WorkingGroup`
- `WorkingAssumption -[:promotedTo]-> Agreement`

> Note: the conceptual lifecycle path `Tdoc → Resolution → CR → Section → Spec` is not realized by a single direct property between `Resolution` and `CR`; the link is reconstructed by joining `Resolution -[:resolutionBelongsTo]-> AgendaItem` with `CR -[:belongsToCRPack]-> CRPack` at the same meeting.

## Vocabulary reuse

- Dublin Core (`dc:title`, `dc:description`, `dc:creator`, `dc:date`, `dc:rights`) and `dcterms:license` — ontology and instance metadata.
- FOAF (`foaf:Person`, `foaf:Organization`) — parent classes for `Contact` and `Company`.

## Axiom summary

- 23 `owl:FunctionalProperty` declarations (at-most-one cardinality)
- 2 `owl:InverseFunctionalProperty` (`hasCR`, `hasTRImpact`)
- 15 inverse property pairs (`owl:inverseOf`) for bidirectional navigation
- 6 `owl:IrreflexiveProperty` covering the section hierarchy (`hasSubSection`, `parentSection`), intra-section references (`referencesSection`, `referencedBySection`), and TR cross-references (`referencesTR`, `referencedByTR`)
- 2 `owl:AsymmetricProperty` on the section hierarchy (`hasSubSection`, `parentSection`)
