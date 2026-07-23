// SpectraCQ RAN4_P1_CQ6-2 (RAN4, phase 1) -- 
// Question: How many meetings are in the dataset? (meeting coverage count).
// Gold: 1 rows, primary column "cnt"

MATCH (m:Meeting) RETURN count(m) AS cnt
