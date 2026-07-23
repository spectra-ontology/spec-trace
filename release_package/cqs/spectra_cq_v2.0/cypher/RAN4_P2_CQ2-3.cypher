// SpectraCQ RAN4_P2_CQ2-3 (RAN4, phase 2) -- CQ2_Tdoc-Resolution
// Question: Find resolutions whose text cites R4- TDocs (in-text reference check).
// Gold: 3 rows, primary column "r.resolutionId"

MATCH (r:Resolution) WHERE r.content IS NOT NULL AND r.content =~ '.*R4-.*' RETURN r.resolutionId, r.content ORDER BY r.resolutionId LIMIT 5
