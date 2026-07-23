// SpectraCQ RAN4_P1_CQ6-5 (RAN4, phase 1) -- 
// Question: How many contacts are in the dataset? (contact count).
// Gold: 1 rows, primary column "cnt"

MATCH (c:Contact) RETURN count(c) AS cnt
