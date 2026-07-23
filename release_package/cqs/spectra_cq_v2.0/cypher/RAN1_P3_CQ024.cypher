// SpectraCQ RAN1_P3_CQ024 (RAN1, phase 3) -- Resolution_TS
// Question: List the 10 most recent agreements affecting TS 38.213 (recent decisions).
// Gold: 10 rows, primary column "agr.resolutionId"

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC, agr.resolutionId LIMIT 10
