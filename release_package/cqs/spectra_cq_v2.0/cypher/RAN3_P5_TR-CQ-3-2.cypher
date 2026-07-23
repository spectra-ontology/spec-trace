// SpectraCQ RAN3_P5_TR-CQ-3-2 (RAN3, phase 5) -- 
// Question: Return TR 38.890's impact on specs 38.401 and 38.423 (targeted-impact review).
// Gold: 12 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.890'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) WHERE s.specNumber IN ['38.401', '38.423'] RETURN s.specNumber, imp.impactType, imp.impactDescription
