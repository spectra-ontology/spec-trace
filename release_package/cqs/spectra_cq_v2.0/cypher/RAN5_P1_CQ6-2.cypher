// SpectraCQ RAN5_P1_CQ6-2 (RAN5, phase 1) -- 
// Question: How many meetings are in the dataset? (corpus size)
// Gold: 1 rows, primary column "cnt"

MATCH (m:Meeting) RETURN count(m) AS cnt
