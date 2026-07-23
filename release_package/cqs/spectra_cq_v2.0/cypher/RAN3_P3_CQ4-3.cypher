// SpectraCQ RAN3_P3_CQ4-3 (RAN3, phase 3) -- CQ4_Resolution
// Question: Trace affected sections through CRs referenced by resolutions (decision-to-section tracing).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(cr:CR) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected <> '' MATCH (cr)-[:MODIFIES]->(sp:Spec) RETURN r.resolutionId, cr.tdocNumber, cr.clausesAffected, sp.specNumber ORDER BY r.resolutionId, cr.tdocNumber, sp.specNumber LIMIT 10
