// SpectraCQ RAN3_P5_TR-CQ-1-3 (RAN3, phase 5) -- 
// Question: Return the conclusions of TR 38.823 (study-outcome review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.823'})
                  RETURN tr.trNumber, tr.conclusions
