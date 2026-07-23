// Multi-hop traceability: for TS 38.214 §5.1.5, which change requests
// modified it (and why), and which technical reports shaped the parent
// specification?
// Cypher twin of ../sparql/MULTI_HOP_traceability.rq — same two-layer chain,
// expressed against the property graph restored by pipeline/load_released_kg.py:
//   CR layer:  (Spec 38.214) <-[:BELONGS_TO_SPEC]- (Section 5.1.5)
//              <-[:MODIFIES_SECTION]- (CR) (.reasonForChange)
//   TR layer:  (Spec 38.214) <-[:IMPACTS_SPEC]- (TRImpact)
//              -[:IMPACT_OF_TR]-> (TechnicalReport)
//
// Modeling note: the released KG carries release-scoped Spec editions
// (e.g. 38.214 Rel-15..Rel-19), which own the Section nodes, plus a
// release-unscoped spec-level node, which receives TRImpact edges. The two
// layers are therefore joined on the natural key specNumber (the same
// property-keyed idiom the benchmark Cypher uses) rather than on one shared
// Spec node — hence the two independent MATCH anchors below.
//
// Coverage note: in the released RAN1 KG, meeting placement is carried by
// Tdoc and Resolution nodes rather than by CR nodes (see CQ1-1 and CQ2-1
// for those hops), so this example chains the CR and TR layers that are
// materialized end-to-end. All constants verified against the released
// RAN1-body.ttl.

MATCH (secSpec:Spec {specNumber: '38.214'})<-[:BELONGS_TO_SPEC]-(sec:Section {sectionNumber: '5.1.5'})<-[:MODIFIES_SECTION]-(cr:CR)
MATCH (trSpec:Spec {specNumber: '38.214'})<-[:IMPACTS_SPEC]-(ti:TRImpact)-[:IMPACT_OF_TR]->(tr:TechnicalReport)
RETURN DISTINCT cr.tdocNumber AS crNumber, cr.reasonForChange AS reasonForChange, tr.trNumber AS trNumber
ORDER BY crNumber, trNumber
