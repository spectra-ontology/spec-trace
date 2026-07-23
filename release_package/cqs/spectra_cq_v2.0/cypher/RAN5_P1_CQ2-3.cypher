// SpectraCQ RAN5_P1_CQ2-3 (RAN5, phase 1) -- 
// Question: Which five Work Items have the most TDocs? (work-item activity)
// Gold: 5 rows, primary column "wi.workItemCode"

MATCH (t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) RETURN wi.workItemCode, count(t) AS cnt ORDER BY cnt DESC LIMIT 5
