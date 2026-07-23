// SpectraCQ RAN4_P1_CQ3-2 (RAN4, phase 1) -- 
// Question: Show the distribution of TDocs by document type (document-type breakdown).
// Gold: 10 rows, primary column "t.type"

MATCH (t:Tdoc) RETURN t.type, count(t) AS cnt ORDER BY cnt DESC LIMIT 10
