// SpectraCQ RAN4_P1_CQ7-2 (RAN4, phase 1) -- 
// Question: How many work items are in the dataset? (work-item count).
// Gold: 1 rows, primary column "cnt"

MATCH (wi:WorkItem) RETURN count(wi) AS cnt
