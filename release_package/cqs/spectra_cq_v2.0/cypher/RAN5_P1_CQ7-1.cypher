// SpectraCQ RAN5_P1_CQ7-1 (RAN5, phase 1) -- 
// Question: How many agenda items are recorded? (agenda count)
// Gold: 1 rows, primary column "cnt"

MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
