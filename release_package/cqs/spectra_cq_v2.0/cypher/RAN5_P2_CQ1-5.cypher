// SpectraCQ RAN5_P2_CQ1-5 (RAN5, phase 2) -- CQ1_Resolution
// Question: How many resolutions relate to each Work Item? (work-item outcome breakdown)
// Gold: 10 rows, primary column "wi_id"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) WITH wi.workItemCode AS wi_id, count(DISTINCT r) AS cnt ORDER BY cnt DESC, wi_id LIMIT 10 RETURN wi_id, cnt
