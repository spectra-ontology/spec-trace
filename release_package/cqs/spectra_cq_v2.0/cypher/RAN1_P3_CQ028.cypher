// SpectraCQ RAN1_P3_CQ028 (RAN1, phase 3) -- Resolution_TS
// Question: Which TS 38.213 resolutions mention HARQ? (tracing HARQ-related decisions)
// Gold: 4 rows, primary column "type"

MATCH (res:Resolution)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE COALESCE(res.contentWithEquations, res.content, '') =~ '(?i).*HARQ.*' MATCH (res)-[:MADE_AT]->(m:Meeting) RETURN [lbl IN ['Resolution','Agreement','Conclusion','WorkingAssumption'] WHERE lbl IN labels(res)] AS type, res.resolutionId, COALESCE(res.contentWithEquations, res.content) AS content, m.meetingNumber ORDER BY m.meetingNumberInt DESC, res.resolutionId LIMIT 10
