// SpectraCQ RAN3_P5_TR-CQ-4-3 (RAN3, phase 5) -- 
// Question: Return TR 38.879's conclusions and its spec impacts (study-to-spec outcome).
// Gold: 6 rows, primary column "tr.conclusions"

MATCH (tr:TechnicalReport {trNumber: '38.879'}) OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.conclusions, s.specNumber, imp.impactType
