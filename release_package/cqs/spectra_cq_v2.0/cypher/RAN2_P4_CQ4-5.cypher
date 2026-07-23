// SpectraCQ RAN2_P4_CQ4-5 (RAN2, phase 4) -- CQ4
// Question: List the change summaries of CRs approved at meeting 132 (meeting change digest).
// Gold: 3 rows, primary column "tdocNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE m.meetingNumberInt = 132 WITH a MATCH (a)-[:REFERENCES]->(c:CR) WHERE c.summaryOfChange IS NOT NULL RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
