// SpectraCQ RAN1_P1_CQ2-2 (RAN1, phase 1) -- CQ2_Tdoc
// Question: For LS out R1-2505678, which group did it originate from and which groups was it sent to and cc'd? (LS routing trace)
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R1-2505678'}) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(orig:WorkingGroup) OPTIONAL MATCH (t)-[:SENT_TO]->(dest:WorkingGroup) OPTIONAL MATCH (t)-[:CC_TO]->(cc:WorkingGroup) RETURN t.tdocNumber, t.title, t.type, orig.wgName AS originated_from, collect(DISTINCT dest.wgName) AS sent_to, collect(DISTINCT cc.wgName) AS cc_to ORDER BY t.tdocNumber ASC LIMIT 10
