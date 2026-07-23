// SpectraCQ RAN4_P1_CQ2-3 (RAN4, phase 1) -- 
// Question: Which Work Items have the most related TDocs? (activity by work item).
// Gold: 5 rows, primary column "wi.workItemCode"

MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
