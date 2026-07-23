// SpectraCQ RAN2_P4_CQ3-2 (RAN2, phase 4) -- CQ3_CRPack
// Question: List the CR packs containing CRs for NR_newRAT work items (pack grouping).
// Gold: 10 rows, primary column "crPackId"

MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
