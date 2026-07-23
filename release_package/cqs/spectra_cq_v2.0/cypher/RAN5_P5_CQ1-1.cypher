// SpectraCQ RAN5_P5_CQ1-1 (RAN5, phase 5) -- 
// Question: List all RAN5 technical reports with their status (TR inventory).
// Gold: 3 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport) RETURN tr.trNumber, tr.trTitle, tr.trStatus ORDER BY tr.trNumber
