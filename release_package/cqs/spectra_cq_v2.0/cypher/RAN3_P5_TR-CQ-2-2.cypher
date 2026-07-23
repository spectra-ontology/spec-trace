// SpectraCQ RAN3_P5_TR-CQ-2-2 (RAN3, phase 5) -- 
// Question: Return the impact types recorded for TR 38.801 (impact-category profile).
// Gold: 1 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.801'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
