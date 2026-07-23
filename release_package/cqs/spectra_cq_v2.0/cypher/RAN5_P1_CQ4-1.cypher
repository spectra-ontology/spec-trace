// SpectraCQ RAN5_P1_CQ4-1 (RAN5, phase 1) -- 
// Question: Trace the revision chain of a TDoc (R5-255xxx) (revision-lineage tracing).
// Gold: 5 rows, primary column "t.tdocNumber"

MATCH (t:Tdoc)-[:IS_REVISION_OF*1..3]->(prev:Tdoc) WHERE t.tdocNumber STARTS WITH 'R5-255' RETURN t.tdocNumber, collect(prev.tdocNumber) AS chain ORDER BY t.tdocNumber LIMIT 5
