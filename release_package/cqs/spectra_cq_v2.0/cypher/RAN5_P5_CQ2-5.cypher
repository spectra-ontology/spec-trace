// SpectraCQ RAN5_P5_CQ2-5 (RAN5, phase 5) -- 
// Question: Which TRs impacted TS 38.521-1, and how? (incoming study impact)
// Gold: 2 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.521-1'}) RETURN tr.trNumber, imp.impactType ORDER BY tr.trNumber
