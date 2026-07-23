// SpectraCQ RAN2_P5_TR-CQ-1-3 (RAN2, phase 5) -- 
// Question: Return the conclusions of TR 38.825 (study outcome).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.825'})
                  RETURN tr.trNumber, tr.conclusions
