// SpectraCQ RAN4_P4_CQ4-5 (RAN4, phase 4) -- CQ4
// Question: List the change summaries of CRs approved at meeting #93 (meeting-scoped change review).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 93}) WITH a MATCH (a)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10
