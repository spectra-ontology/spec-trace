// SpectraCQ RAN2_P2_CQ3-3 (RAN2, phase 2) -- CQ3
// Question: Return the top companies by resolution contribution per work item (technology leadership).
// Gold: 5 rows, primary column "wi.workItemCode"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:RELATED_TO]->(wi:WorkItem), (t)-[:SUBMITTED_BY]->(c:Company) WITH wi, c, count(DISTINCT r) AS cnt ORDER BY cnt DESC WITH wi, collect({company: c.companyName, count: cnt})[0..5] AS topCompanies RETURN wi.workItemCode, topCompanies ORDER BY wi.workItemCode LIMIT 5
