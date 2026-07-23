// SpectraCQ RAN4_P5_CQ1-2 (RAN4, phase 5) -- 
// Question: Return the scope of TR 38.803 (study-scope review).
// Gold: 1 rows, primary column "tr.trNumber"

MATCH (tr:TechnicalReport {trNumber: '38.803'}) RETURN tr.trNumber, tr.scope
