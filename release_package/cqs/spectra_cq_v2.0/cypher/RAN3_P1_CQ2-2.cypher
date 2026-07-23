// SpectraCQ RAN3_P1_CQ2-2 (RAN3, phase 1) -- CQ2_Tdoc
// Question: Trace where LS R3-258479 came from and where it was sent, including CC (liaison-flow tracing).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-258479'}) OPTIONAL MATCH (t)-[:SENT_TO]->(wg:WorkingGroup) OPTIONAL MATCH (t)-[:CC_TO]->(cc:WorkingGroup) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(from:WorkingGroup) RETURN t.tdocNumber, t.direction, collect(DISTINCT wg.wgName) AS sentTo, collect(DISTINCT cc.wgName) AS ccTo, collect(DISTINCT from.wgName) AS originatedFrom
