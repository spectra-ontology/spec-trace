// SpectraCQ RAN2_P2_CQ1-7 (RAN2, phase 2) -- CQ1_Resolution
// Question: List the resolutions tied to a given work item via its TDocs (work-item decision trace).
// Gold: 10 rows, primary column "workItemId"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (r)-[:MADE_AT]->(m:Meeting) WITH wi, r, m RETURN wi.workItemCode AS workItemId, r.resolutionId, m.canonicalMeetingNumber ORDER BY m.meetingNumberInt DESC, wi.workItemCode, r.resolutionId LIMIT 10
