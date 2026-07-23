// SpectraCQ RAN5_P3_CQ5-2 (RAN5, phase 3) -- CQ5
// Question: Show each company's CR contributions per RAN5 spec (contribution matrix).
// Gold: 10 rows, primary column "company"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' WITH c.companyName AS company, sp.specNumber AS spec, count(cr) AS cnt ORDER BY cnt DESC RETURN company, spec, cnt LIMIT 10
