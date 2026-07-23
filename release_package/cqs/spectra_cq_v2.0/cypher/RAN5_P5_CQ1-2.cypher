// SpectraCQ RAN5_P5_CQ1-2 (RAN5, phase 5) -- 
// Question: Return the scope of TR 38.903 (study-scope review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.903'}) RETURN tr.trNumber, tr.scope
