// SpectraCQ RAN3_P2_CQ2-2 (RAN3, phase 2) -- CQ2_Tdoc-Resolution
// Question: List resolutions that reference five or more TDocs (multi-document decisions).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r, collect(t.tdocNumber) AS refs, count(t) AS cnt WHERE cnt >= 5 MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, refs[..5] AS top5_refs, cnt ORDER BY m.meetingNumberInt DESC, cnt DESC LIMIT 10
