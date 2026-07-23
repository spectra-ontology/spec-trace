// SpectraCQ RAN1_P2_CQ1-5 (RAN1, phase 2) -- CQ1_Resolution
// Question: List recent agreements carrying an FFS (Further For Study) marker (items needing further study).
// Gold: 15 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.hasFFS = true RETURN a.resolutionId, a.content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 15
