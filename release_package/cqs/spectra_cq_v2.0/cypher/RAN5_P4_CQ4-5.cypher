// SpectraCQ RAN5_P4_CQ4-5 (RAN5, phase 4) -- CQ4
// Question: List the change summaries of CRs referenced by conclusions at meeting #87 (meeting-level change review).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (con:Conclusion)-[:MADE_AT]->(m:Meeting {meetingNumberInt: 87}) WITH con MATCH (con)-[:REFERENCES]->(t:Tdoc) WHERE t.summaryOfChange IS NOT NULL RETURN t.tdocNumber AS tdocNumber, t.summaryOfChange AS summary ORDER BY t.tdocNumber DESC LIMIT 10
