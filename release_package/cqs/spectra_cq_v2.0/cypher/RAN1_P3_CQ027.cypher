// SpectraCQ RAN1_P3_CQ027 (RAN1, phase 3) -- Resolution_TS
// Question: Are there agreements that reference CRs across multiple TSs at once? (cross-TS decisions)
// Gold: 10 rows, primary column "agr.resolutionId"

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH agr, collect(DISTINCT sp.specNumber) AS specs WHERE size(specs) > 1 MATCH (agr)-[:MADE_AT]->(m:Meeting) RETURN agr.resolutionId, specs, m.meetingNumber ORDER BY m.meetingNumberInt DESC, agr.resolutionId LIMIT 10
