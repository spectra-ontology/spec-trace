// SpectraCQ RAN1_P3_CQ020 (RAN1, phase 3) -- CR_TS
// Question: List the CRs Qualcomm submitted against TS 38.214 (its areas of contribution).
// Gold: 20 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.214'}) MATCH (cr)-[:SUBMITTED_BY]->(co:Company) WHERE co.companyName CONTAINS 'Qualcomm' MATCH (cr)-[:PRESENTED_AT]->(m:Meeting) RETURN cr.tdocNumber, cr.title, m.meetingNumber ORDER BY m.meetingNumberInt DESC, cr.tdocNumber LIMIT 20
