// SpectraCQ RAN5_P1_CQ7-2 (RAN5, phase 1) -- 
// Question: How many Work Items are recorded? (work-item count)
// Gold: 1 rows, primary column "cnt"

MATCH (wi:WorkItem) RETURN count(wi) AS cnt
