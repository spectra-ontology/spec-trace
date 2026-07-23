// SpectraCQ RAN3_P3_CQ4-2 (RAN3, phase 3) -- CQ4_Resolution
// Question: Return the resolutions approving CRs that modify spec 38.423 (approval provenance).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.423'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
