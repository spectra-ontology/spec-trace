// SpectraCQ RAN2_P2_CQ1-9 (RAN2, phase 2) -- CQ1_Resolution
// Question: Return the total counts by resolution type (Agreement / Conclusion / WorkingAssumption) (decision mix).
// Gold: 3 rows, primary column "type"

MATCH (r:Resolution) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' END AS type, count(r) AS cnt ORDER BY cnt DESC
