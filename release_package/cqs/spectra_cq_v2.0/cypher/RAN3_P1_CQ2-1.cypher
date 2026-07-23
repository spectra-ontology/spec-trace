// SpectraCQ RAN3_P1_CQ2-1 (RAN3, phase 1) -- CQ2_Tdoc
// Question: Return the predecessor revision of TDoc R3-241531 (revision-lineage tracing).
// Gold: 1 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc {tdocNumber: 'R3-241531'})-[:IS_REVISION_OF]->(prev:Tdoc) RETURN t.tdocNumber, prev.tdocNumber, prev.title
