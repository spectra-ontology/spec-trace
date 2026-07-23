// SpectraCQ RAN4_P1_CQ7-1 (RAN4, phase 1) -- 
// Question: How many agenda items are in the dataset? (agenda-item count).
// Gold: 1 rows, primary column "cnt"

MATCH (ai:AgendaItem) RETURN count(ai) AS cnt
