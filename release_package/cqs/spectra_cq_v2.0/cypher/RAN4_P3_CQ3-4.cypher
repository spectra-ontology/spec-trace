// SpectraCQ RAN4_P3_CQ3-4 (RAN4, phase 3) -- CQ3_CR
// Question: List CRs on spec 38.133 that touch clause 4.2 (clause-level change filter).
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}) WHERE cr.clausesAffected CONTAINS '4.2' RETURN cr.tdocNumber, cr.clausesAffected ORDER BY cr.tdocNumber DESC LIMIT 10
