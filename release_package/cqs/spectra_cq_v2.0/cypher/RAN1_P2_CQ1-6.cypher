// SpectraCQ RAN1_P2_CQ1-6 (RAN1, phase 2) -- CQ1_Resolution
// Question: What was agreed on PDCCH blind decoding? (PDCCH decisions)
// Gold: 10 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS 'PDCCH' AND a.content CONTAINS 'blind' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 10
