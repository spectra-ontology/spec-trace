// SpectraCQ RAN4_P1_CQ5-1 (RAN4, phase 1) -- 
// Question: Return node counts by label across the graph (dataset statistics).
// Gold: 27 rows, primary column "label"

MATCH (n) UNWIND labels(n) AS label RETURN label, count(*) AS cnt ORDER BY cnt DESC, label
