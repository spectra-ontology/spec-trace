// SpectraCQ RAN3_P5_TR-CQ-4-2 (RAN3, phase 5) -- 
// Question: Return the status and scope of TR 38.743 (study status and scope).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.743'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
