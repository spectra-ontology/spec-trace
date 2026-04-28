// SpectraCQ P1_CQ2-1 — CQ2_Tdoc관계추적
// Question (English): Return the revision history (predecessor/successor versions) of TDoc R1-2599001 (revision-lineage tracing).
// Schema area: classes=['Tdoc'], rels=['IS_REVISION_OF', 'REVISED_TO']

MATCH (t:Tdoc {tdocNumber: 'R1-2599001'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN prev.tdocNumber AS previous, t.tdocNumber AS current, t.title, next.tdocNumber AS revised_to ORDER BY t.tdocNumber ASC LIMIT 10
