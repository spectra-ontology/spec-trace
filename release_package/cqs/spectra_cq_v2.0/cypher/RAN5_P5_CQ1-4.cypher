// SpectraCQ RAN5_P5_CQ1-4 (RAN5, phase 5) -- 
// Question: List the technical reports marked Completed (finished-study survey).
// Gold: 3 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport) WHERE tr.trStatus = 'Completed' RETURN tr.trNumber, tr.trTitle ORDER BY tr.trNumber
