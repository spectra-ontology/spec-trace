// SpectraCQ RAN2_P5_TR-CQ-2-1 (RAN2, phase 5) -- 
// Question: List the specs impacted by TR 38.825 with their impact type (study-to-spec impact).
// Gold: 2 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.825'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN s.specNumber, imp.impactType
