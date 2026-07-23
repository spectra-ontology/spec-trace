// SpectraCQ RAN2_P1_CQ2-1 (RAN2, phase 1) -- CQ2_Tdoc
// Question: Return the predecessor and successor revisions of TDoc R2-2509478 (revision-lineage tracing).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R2-2509478'}) OPTIONAL MATCH (t)-[:IS_REVISION_OF]->(prev:Tdoc) OPTIONAL MATCH (t)-[:REVISED_TO]->(next:Tdoc) RETURN t.tdocNumber, prev.tdocNumber AS previousVersion, next.tdocNumber AS nextVersion
