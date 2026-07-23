// SpectraCQ RAN1_P3_CQ026 (RAN1, phase 3) -- Resolution_TS
// Question: Which TS 38.213 agreements still carry a TBD? (technical issues not yet settled)
// Gold: 1 rows, primary column "agr.resolutionId"

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE agr.hasTBD = true MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC LIMIT 10
