// SpectraCQ RAN5_P1_CQ5-3 (RAN5, phase 1) -- 
// Question: How many TDocs have a submitting company recorded? (attribution coverage)
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc) OPTIONAL MATCH (t)-[:SUBMITTED_BY]->(c:Company) RETURN count(t) AS total, count(c) AS withCompany
