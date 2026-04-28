// SpectraCQ P3_CQ027 — Resolution_TS_의사결정
// Question (English): Return Agreements that simultaneously reference CRs across multiple TSes (cross-TS consensus).
// Schema area: classes=['Agreement', 'CR', 'Meeting', 'Spec'], rels=['MADE_AT', 'MODIFIES', 'REFERENCES']

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH agr, collect(DISTINCT sp.specNumber) AS specs WHERE size(specs) > 1 MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN agr.resolutionId, specs, m.meetingNumber ORDER BY m.meetingNumberInt DESC LIMIT 10
