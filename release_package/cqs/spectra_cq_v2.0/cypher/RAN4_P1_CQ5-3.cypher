// SpectraCQ RAN4_P1_CQ5-3 (RAN4, phase 1) -- 
// Question: How many TDocs have a submitting company assigned? (attribution coverage check).
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
