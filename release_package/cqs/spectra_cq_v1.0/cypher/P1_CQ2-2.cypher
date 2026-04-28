// SpectraCQ P1_CQ2-2 — CQ2_Tdoc관계추적
// Question (English): For outgoing LS R1-2599567, return its origin (originatedFrom) and destination (sentTo) Working Groups (LS-path tracing).
// Schema area: classes=['Tdoc', 'WorkingGroup'], rels=['CC_TO', 'ORIGINATED_FROM', 'SENT_TO']

MATCH (t:Tdoc {tdocNumber: 'R1-2599567'}) OPTIONAL MATCH (t)-[:ORIGINATED_FROM]->(orig:WorkingGroup) OPTIONAL MATCH (t)-[:SENT_TO]->(dest:WorkingGroup) OPTIONAL MATCH (t)-[:CC_TO]->(cc:WorkingGroup) RETURN t.tdocNumber, t.title, t.type, orig.wgName AS originated_from, collect(DISTINCT dest.wgName) AS sent_to, collect(DISTINCT cc.wgName) AS cc_to ORDER BY t.tdocNumber ASC LIMIT 10
