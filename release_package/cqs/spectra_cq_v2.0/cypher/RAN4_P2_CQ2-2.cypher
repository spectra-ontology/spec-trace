// SpectraCQ RAN4_P2_CQ2-2 (RAN4, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which resolutions reference 5 or more TDocs? (broad-scope decisions).
// Gold: 10 rows, primary column "r.resolutionId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH r, collect(t.tdocNumber) AS refs, count(t) AS cnt WHERE cnt >= 5 MATCH (r)-[:MADE_AT]->(m:Meeting) RETURN r.resolutionId, m.canonicalMeetingNumber, refs[..5] AS top5_refs, cnt ORDER BY m.meetingNumberInt DESC, cnt DESC LIMIT 10
