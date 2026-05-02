---
name: Ontology — propose a class, property, or axiom extension
about: Suggest an addition or modification to the SPECTRA OWL ontology
title: "[ONTOLOGY] <one-line summary>"
labels: ontology, enhancement
assignees: ''
---

Use this template to propose extending or modifying **`ontology/spectra.ttl`**
(the SPECTRA OWL schema). Each proposal should explain *why* the schema gap
exists and *which CQ(s)* the extension would enable.

## Proposal type

- [ ] New class (under which superclass?)
- [ ] New object property (domain → range)
- [ ] New data property (domain → datatype)
- [ ] New axiom (functional / inverse / disjointness / subclass / etc.)
- [ ] Modification of existing element

## Element spec

<!-- e.g., -->
<!-- spectra:WorkPlan a owl:Class ; -->
<!--     rdfs:subClassOf spectra:WorkItem ; -->
<!--     rdfs:label "Work Plan" ; -->
<!--     rdfs:comment "A multi-meeting plan tracking a feature across releases." -->

## Motivation

### Which competency question does this enable?

<!-- Reference an existing CQ ID from cqs/spectra_cq_v1.0/, or attach a new -->
<!-- CQ proposal (see cq-request.md template). -->

### Source-data evidence

<!-- Where in the 3GPP corpus does this concept appear? -->
<!-- e.g., "Work Plan" entries appear in RAN plenary chairman notes Sect. 6.X -->

## Cross-WG check

<!-- Does this concept exist across all RAN WGs (1-5), or only a subset? -->
<!-- The schema-diff protocol expects evidence across at least RAN1 + 2 sibling WGs -->
<!-- before promoting to ontology-level (vs. loader-local) status. -->

- [ ] RAN1
- [ ] RAN2
- [ ] RAN3
- [ ] RAN4
- [ ] RAN5

## Potential conflicts

<!-- Does this overlap with an existing class/property? Check tab:crosswg-reuse -->
<!-- and cross_wg_schema_diff.json before proposing. -->

## Backwards compatibility

<!-- Does the change break existing instantiation? If so, propose a migration. -->
