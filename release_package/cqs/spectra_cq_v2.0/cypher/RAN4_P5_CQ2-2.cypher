// SpectraCQ RAN4_P5_CQ2-2 (RAN4, phase 5) -- 
// Question: Return the impact types of TR 38.860 (impact classification).
// Gold: 1 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.860'})-[:HAS_TR_IMPACT]->(imp:TRImpact) RETURN imp.impactType, imp.impactDescription
