// SpectraCQ RAN5_P1_CQ3-2 (RAN5, phase 1) -- 
// Question: Break down TDocs by type (document-type distribution).
// Gold: 10 rows, primary column "t.type"

MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
