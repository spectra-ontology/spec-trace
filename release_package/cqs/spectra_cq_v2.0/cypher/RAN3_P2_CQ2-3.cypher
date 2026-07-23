// SpectraCQ RAN3_P2_CQ2-3 (RAN3, phase 2) -- CQ2_Tdoc-Resolution
// Question: Find resolutions whose text cites R3- TDoc numbers (in-text reference check).
// Gold: 3 rows, primary column "r.resolutionId"

MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '.*R3-.*' RETURN r.resolutionId, r.content ORDER BY r.resolutionId LIMIT 5
