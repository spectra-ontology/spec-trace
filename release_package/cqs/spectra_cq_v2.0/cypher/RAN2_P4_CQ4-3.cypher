// SpectraCQ RAN2_P4_CQ4-3 (RAN2, phase 4) -- CQ4
// Question: List the sections modified by CRs for NR_newRAT work items (work-item section footprint).
// Gold: 10 rows, primary column "sectionId"

MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
