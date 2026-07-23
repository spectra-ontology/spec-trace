// SpectraCQ RAN2_P1_CQ3-4 (RAN2, phase 1) -- CQ3
// Question: Return Samsung's contribution adoption rate (success-rate benchmarking).
// Gold: 1 rows, primary column "total"

MATCH (t:Tdoc)-[:SUBMITTED_BY]->(c:Company {companyName: 'Samsung'}) WITH count(t) AS total, sum(CASE WHEN t.status IN ['agreed', 'approved', 'endorsed'] THEN 1 ELSE 0 END) AS adopted RETURN total, adopted, round(adopted * 100.0 / total, 1) AS adoptionRate
