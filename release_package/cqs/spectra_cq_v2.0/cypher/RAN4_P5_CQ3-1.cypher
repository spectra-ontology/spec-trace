// SpectraCQ RAN4_P5_CQ3-1 (RAN4, phase 5) -- 
// Question: Which specs did the NR RF study TR 38.803 impact? (study-to-spec impact).
// Gold: 4 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.803'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
