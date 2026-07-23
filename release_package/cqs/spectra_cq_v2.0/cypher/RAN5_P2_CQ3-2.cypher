// SpectraCQ RAN5_P2_CQ3-2 (RAN5, phase 2) -- CQ3
// Question: Show each company's resolution contributions per Work Item (technology contribution breakdown).
// Gold: 10 rows, primary column "wi_id"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem) MATCH (t)-[:SUBMITTED_BY]->(c:Company) WITH wi.workItemCode AS wi_id, c.companyName AS company, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN wi_id, company, cnt
