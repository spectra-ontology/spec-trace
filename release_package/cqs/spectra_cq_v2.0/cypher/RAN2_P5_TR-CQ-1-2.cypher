// SpectraCQ RAN2_P5_TR-CQ-1-2 (RAN2, phase 5) -- 
// Question: Return the scope of TR 38.825 (study-scope lookup).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.825'})
                  RETURN tr.trNumber, tr.scope
