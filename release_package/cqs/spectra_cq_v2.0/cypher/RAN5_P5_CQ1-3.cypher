// SpectraCQ RAN5_P5_CQ1-3 (RAN5, phase 5) -- 
// Question: Return the conclusions of TR 38.918 (study-outcome review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.918'}) WHERE tr.conclusions IS NOT NULL RETURN tr.trNumber, tr.conclusions
