// SpectraCQ RAN4_P5_CQ1-3 (RAN4, phase 5) -- 
// Question: Return the conclusions of TR 38.785 (study-outcome review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.785'}) WHERE tr.conclusions IS NOT NULL RETURN tr.trNumber, tr.conclusions
