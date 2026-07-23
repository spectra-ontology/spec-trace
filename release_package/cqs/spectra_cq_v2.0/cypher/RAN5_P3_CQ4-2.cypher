// SpectraCQ RAN5_P3_CQ4-2 (RAN5, phase 3) -- CQ4_Resolution
// Question: List the conclusions that reference CRs modifying TS 38.521-1 (decision provenance).
// Gold: 4 rows, primary column "res.resolutionId"

MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec {specNumber: '38.521-1'}) RETURN res.resolutionId, t.tdocNumber ORDER BY res.resolutionId DESC LIMIT 10
