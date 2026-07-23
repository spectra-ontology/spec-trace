// SpectraCQ RAN1_P4_CQ4-5 (RAN1, phase 4) -- CQ4
// Question: Summarize the changes across the CRs agreed at meeting RAN1#121 (consolidated summary-of-change).
// Gold: 15 rows, primary column "m.meetingNumber"

MATCH (res:Resolution)-[:MADE_AT]->(m:Meeting {meetingNumber: 'RAN1#121'}) MATCH (res)-[:REFERENCES]->(cr:CR) WHERE cr.summaryOfChange IS NOT NULL RETURN m.meetingNumber, res.resolutionId, cr.tdocNumber, cr.summaryOfChange ORDER BY cr.tdocNumber DESC LIMIT 15
