// SpectraCQ RAN5_P5_CQ3-1 (RAN5, phase 5) -- 
// Question: Detail how TR 38.903 impacted each spec (full impact breakdown).
// Gold: 5 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.903'})-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec) RETURN tr.trNumber, s.specNumber, imp.impactType, imp.impactDescription ORDER BY s.specNumber
