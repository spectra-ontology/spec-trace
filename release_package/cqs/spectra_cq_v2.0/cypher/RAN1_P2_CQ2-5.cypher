// SpectraCQ RAN1_P2_CQ2-5 (RAN1, phase 2) -- CQ2_Tdoc-Resolution
// Question: List the resolutions related to changes to TS 38.211 (revision history of 38.211).
// Gold: 15 rows, primary column "a.resolutionId"

MATCH (a:Agreement)-[:MADE_AT]->(m:Meeting) WHERE a.content CONTAINS '38.211' RETURN a.resolutionId, m.meetingNumber, a.content ORDER BY m.meetingNumberInt DESC, a.resolutionId LIMIT 15
