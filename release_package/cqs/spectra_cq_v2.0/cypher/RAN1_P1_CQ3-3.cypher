// SpectraCQ RAN1_P1_CQ3-3 (RAN1, phase 1) -- CQ3
// Question: Which companies contributed most to Work Item NR_unlic-Core (NR-U)? Top 10 by TDoc count (competitive landscape).
// Gold: 10 rows, primary column "c.companyName"

MATCH (c:Company)<-[:SUBMITTED_BY]-(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_unlic-Core'}) RETURN c.companyName, count(t) AS tdocCount ORDER BY tdocCount DESC, c.companyName ASC LIMIT 10
