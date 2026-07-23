// SpectraCQ RAN5_P5_CQ2-1 (RAN5, phase 5) -- 
// Question: Which specs did TR 38.903 impact, and how? (study-to-spec impact)
// Gold: 5 rows, primary column "s.specNumber"

MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN s.specNumber, imp.impactType ORDER BY s.specNumber
