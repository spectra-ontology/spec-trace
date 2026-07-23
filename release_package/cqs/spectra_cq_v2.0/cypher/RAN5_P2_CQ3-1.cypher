// SpectraCQ RAN5_P2_CQ3-1 (RAN5, phase 2) -- CQ3
// Question: Which ten companies submitted the most resolution-referenced TDocs? (influence ranking)
// Gold: 10 rows, primary column "company"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company) WITH c.companyName AS company, count(DISTINCT r) AS resolution_count ORDER BY resolution_count DESC, company LIMIT 10 RETURN company, resolution_count
