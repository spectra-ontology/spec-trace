// SpectraCQ RAN2_P1_CQ2-2 (RAN2, phase 1) -- CQ2_Tdoc
// Question: Trace where liaison statement R2-2509443 originated and where it was sent (LS routing).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509443'}) OPTIONAL MATCH (t)-[:SENT_TO]->(wg:WorkingGroup) OPTIONAL MATCH (t)-[:CC_TO]->(cc:WorkingGroup) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(from:WorkingGroup) RETURN t.tdocNumber, t.direction, collect(DISTINCT wg.wgName) AS sentTo, collect(DISTINCT cc.wgName) AS ccTo, collect(DISTINCT from.wgName) AS originatedFrom
