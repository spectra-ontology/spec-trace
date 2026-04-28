// SpectraCQ P3_CQ026 — Resolution_TS_의사결정
// Question (English): Return Agreements affecting TS 38.213 that contain TBD markers (unresolved technical issues).
// Schema area: classes=['Agreement', 'CR', 'Meeting', 'Spec'], rels=['MADE_AT', 'MODIFIES', 'REFERENCES']

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.213'}) WHERE agr.hasTBD = true MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN DISTINCT agr.resolutionId, COALESCE(agr.contentWithEquations, agr.content) AS content, m.meetingNumber, m.meetingNumberInt ORDER BY m.meetingNumberInt DESC LIMIT 10
