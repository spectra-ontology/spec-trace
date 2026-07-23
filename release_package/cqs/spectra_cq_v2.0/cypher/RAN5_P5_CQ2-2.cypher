// SpectraCQ RAN5_P5_CQ2-2 (RAN5, phase 5) -- 
// Question: Return the impact types and descriptions for TR 38.905 (impact classification).
// Gold: 3 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.905'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
