// SpectraCQ RAN1_P3_CQ018 (RAN1, phase 3) -- CR_TS
// Question: Which CRs affect TS 38.214 Section 5.1? List CRs whose affected clauses include 5.1 (impact on my implementation).
// Gold: 15 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) WHERE cr.clausesAffected IS NOT NULL AND cr.clausesAffected CONTAINS '5.1' MATCH (cr)-[:SUBMITTED_BY]->(co:Company) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, cr.clausesAffected, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 15
