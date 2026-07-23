// SpectraCQ RAN3_P1_CQ3-4 (RAN3, phase 1) -- CQ3
// Question: Return the share of Samsung's TDocs that were agreed (success-rate metric).
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) WITH count(t) AS total MATCH (t2:Tdoc)-[:SUBMITTED_BY]->(c2:Company {companyName: 'Samsung'}) WHERE t2.status = 'agreed' RETURN total, count(t2) AS agreed, toFloat(count(t2)) / total AS ratio
