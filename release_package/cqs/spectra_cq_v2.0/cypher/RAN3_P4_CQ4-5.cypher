// SpectraCQ RAN3_P4_CQ4-5 (RAN3, phase 4) -- CQ4
// Question: List the change summaries of CRs approved at meeting RAN3#123 (meeting-outcome review).
// Gold: 10 rows, primary column "c.tdocNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumberInt = 123 WITH a MATCH (a)-[:REFERENCES]->(c:CR) WHERE c.reasonForChange IS NOT NULL RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
