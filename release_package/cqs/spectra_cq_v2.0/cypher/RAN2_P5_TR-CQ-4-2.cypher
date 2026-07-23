// SpectraCQ RAN2_P5_TR-CQ-4-2 (RAN2, phase 5) -- 
// Question: Return the status and study scope of TR 38.744 (study snapshot).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.744'})
                  RETURN tr.trNumber, tr.trStatus, tr.scope
