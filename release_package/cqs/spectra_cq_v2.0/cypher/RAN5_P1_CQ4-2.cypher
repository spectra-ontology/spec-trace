// SpectraCQ RAN5_P1_CQ4-2 (RAN5, phase 1) -- 
// Question: For each liaison statement (LS), show its direction and recipient working groups (LS routing analysis).
// Gold: 5 rows, primary column "ls.tdocNumber"

MATCH (ls:LS) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo ORDER BY ls.tdocNumber, ls.direction LIMIT 5
