// SpectraCQ RAN5_P1_CQ6-5 (RAN5, phase 1) -- 
// Question: How many Contact nodes exist? (contact count)
// Gold: 1 rows, primary column "cnt"

MATCH (c:Contact) RETURN count(c) AS cnt
