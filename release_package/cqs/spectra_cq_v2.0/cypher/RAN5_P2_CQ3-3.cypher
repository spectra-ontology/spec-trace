// SpectraCQ RAN5_P2_CQ3-3 (RAN5, phase 2) -- CQ3
// Question: Rank the main contributors to each spec's resolutions (spec contributor ranking).
// Gold: 10 rows, primary column "spec"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) MATCH (t)-[:SUBMITTED_BY]->(c:Company) WITH s.specNumber AS spec, c.companyName AS company, count(DISTINCT t) AS tdoc_count ORDER BY tdoc_count DESC LIMIT 10 RETURN spec, company, tdoc_count
