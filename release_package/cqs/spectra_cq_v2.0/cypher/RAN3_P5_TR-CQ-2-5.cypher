// SpectraCQ RAN3_P5_TR-CQ-2-5 (RAN3, phase 5) -- 
// Question: List the TRs that impacted spec 38.401 (spec-provenance in studies).
// Gold: 36 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec {specNumber: '38.401'}) RETURN tr.trNumber, imp.impactType, imp.impactDescription
