// SpectraCQ RAN3_P5_TR-CQ-3-3 (RAN3, phase 5) -- 
// Question: Return TR 38.743's impact on spec 38.423 (targeted-impact review).
// Gold: 6 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.743'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.423'}) RETURN imp.impactType, imp.impactDescription
