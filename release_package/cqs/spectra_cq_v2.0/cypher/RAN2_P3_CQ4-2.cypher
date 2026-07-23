// SpectraCQ RAN2_P3_CQ4-2 (RAN2, phase 3) -- CQ4_Resolution
// Question: Which resolutions approved the CRs that modify spec 38.331 (approval trace)?
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.331'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
