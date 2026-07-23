// SpectraCQ RAN2_P5_TR-CQ-4-3 (RAN2, phase 5) -- 
// Question: Return the conclusions of TR 38.835 and the specs they fed into (outcome-to-spec).
// Gold: 1 rows, primary column "tr.conclusions"

MATCH (tr:TechnicalReport {trNumber: '38.835'})
                  OPTIONAL MATCH (tr)-[:HAS_TR_IMPACT]->(imp:TRImpact)-[:IMPACTS_SPEC]->(s:Spec)
                  RETURN tr.conclusions, collect({spec: s.specNumber, type: imp.impactType}) AS impacts
