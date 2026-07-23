// SpectraCQ RAN4_P1_CQ4-2 (RAN4, phase 1) -- 
// Question: Return the direction and recipients of liaison statement R4-2417507 (LS routing analysis).
// Gold: 1 rows, primary column "ls.tdocNumber"

MATCH (ls:LS {tdocNumber:'R4-2417507'}) OPTIONAL MATCH (ls)-[:SENT_TO]->(wg:WorkingGroup) RETURN ls.tdocNumber, ls.direction, collect(wg.wgName) AS sentTo
