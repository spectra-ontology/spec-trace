// SpectraCQ RAN5_P2_CQ1-4 (RAN5, phase 2) -- CQ1_Resolution
// Question: How many resolutions touch each modified spec? (spec-outcome breakdown)
// Gold: 10 rows, primary column "spec"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH s.specNumber AS spec, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN spec, cnt
