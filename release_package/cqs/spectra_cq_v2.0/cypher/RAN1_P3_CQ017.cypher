// SpectraCQ RAN1_P3_CQ017 (RAN1, phase 3) -- CR_TS
// Question: List the 20 most recent CRs modifying TS 38.213 (recent changes).
// Gold: 20 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN cr.tdocNumber, cr.title, co.companyName, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 20
