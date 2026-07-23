// SpectraCQ RAN5_P3_CQ4-1 (RAN5, phase 3) -- CQ4_Resolution
// Question: Which RAN5 specs are modified by CRs that conclusions reference? (outcome-to-spec trace)
// Gold: 10 rows, primary column "res.resolutionId"

MATCH (res:Conclusion)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN res.resolutionId, t.tdocNumber, sp.specNumber ORDER BY res.resolutionId DESC LIMIT 10
