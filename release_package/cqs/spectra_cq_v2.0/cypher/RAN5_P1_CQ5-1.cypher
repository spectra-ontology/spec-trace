// SpectraCQ RAN5_P1_CQ5-1 (RAN5, phase 1) -- 
// Question: Report node counts by label across the graph (dataset overview).
// Gold: 22 rows, primary column "label"

MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
