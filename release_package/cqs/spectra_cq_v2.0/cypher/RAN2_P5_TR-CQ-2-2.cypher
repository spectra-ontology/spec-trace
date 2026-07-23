// SpectraCQ RAN2_P5_TR-CQ-2-2 (RAN2, phase 5) -- 
// Question: Return the impact-type breakdown of TR 38.804 (impact profile).
// Gold: 1 rows, primary column "imp.impactType"

MATCH (tr:TechnicalReport {trNumber: '38.804'})-[:HAS_TR_IMPACT]->(imp:TRImpact)
                  RETURN imp.impactType, count(imp) AS cnt
