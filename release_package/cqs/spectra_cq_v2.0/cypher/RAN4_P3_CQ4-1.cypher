// SpectraCQ RAN4_P3_CQ4-1 (RAN4, phase 3) -- CQ4_Resolution
// Question: List the resolutions and the approved CRs that modify spec 38.133 (decision-to-change trace).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) RETURN r.resolutionId, cr.tdocNumber ORDER BY r.resolutionId DESC LIMIT 10
