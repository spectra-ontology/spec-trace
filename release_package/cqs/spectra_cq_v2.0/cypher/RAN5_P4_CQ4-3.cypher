// SpectraCQ RAN5_P4_CQ4-3 (RAN5, phase 4) -- CQ4
// Question: Which sections do the 5GS_NR_LTE-UEConTest CRs modify? (work-item clause impact)
// Gold: 10 rows, primary column "sectionId"

MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:MODIFIES_SECTION]->(sec:Section) RETURN DISTINCT sec.sectionId AS sectionId ORDER BY sec.sectionId LIMIT 10
