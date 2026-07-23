// SpectraCQ RAN5_P1_CQ6-4 (RAN5, phase 1) -- 
// Question: How many liaison statements (LS) are recorded? (LS count)
// Gold: 1 rows, primary column "cnt"

MATCH (ls:LS) RETURN count(ls) AS cnt
