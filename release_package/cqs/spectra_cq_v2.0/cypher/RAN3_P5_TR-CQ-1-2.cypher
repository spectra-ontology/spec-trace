// SpectraCQ RAN3_P5_TR-CQ-1-2 (RAN3, phase 5) -- 
// Question: Return the scope of TR 38.823 (study-scope review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.823'})
                  RETURN tr.trNumber, tr.scope
