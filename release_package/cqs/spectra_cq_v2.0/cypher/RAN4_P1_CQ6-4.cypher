// SpectraCQ RAN4_P1_CQ6-4 (RAN4, phase 1) -- 
// Question: How many liaison statements are in the dataset? (LS count).
// Gold: 1 rows, primary column "cnt"

MATCH (ls:LS) RETURN count(ls) AS cnt
