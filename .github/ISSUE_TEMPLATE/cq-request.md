---
name: SpectraCQ — propose a new competency question
about: Suggest a new competency question for the SpectraCQ benchmark
title: "[CQ] <one-line summary>"
labels: spectraCQ, enhancement
assignees: ''
---

Use this template to propose adding a new competency question to **SpectraCQ v1.0**
(the 137-CQ companion dataset shipped with the SPECTRA ontology).

## Question (English)

<!-- A natural-language question a standards engineer would actually ask. -->

## Schema area

<!-- Which schema concern does this exercise? Pick one or more: -->
<!-- contributions / resolutions / specifications / cross-group communication -->

## Phase

<!-- The five-phase progression of SpectraCQ: P1=core lifecycle, P2=resolution -->
<!-- bookkeeping, P3=spec-structure traceability, P4=CR analytics, P5=TR impact. -->
<!-- See Section 5 of the paper. -->

P:

## Cypher draft (Neo4j) — optional but encouraged

```cypher
// e.g., MATCH (cr:CR)-[:MODIFIES]->(:Spec {specNumber:'38.214'}) ...
```

## Why this CQ matters

<!-- One or two sentences: which traceability task does this support, and -->
<!-- why is it not already covered by an existing CQ? -->

## Verification path

<!-- If you have access to a SPECTRA-conformant KG, please indicate: -->
<!-- - WG used: RAN1 / RAN2 / RAN3 / RAN4 / RAN5 -->
<!-- - Number of result rows: -->
<!-- - Sample result row: -->

## Anonymization

<!-- If the question references concrete companies, please replace them with -->
<!-- "Company X", "Company Y" etc. so the CQ stays portable across organisations. -->
