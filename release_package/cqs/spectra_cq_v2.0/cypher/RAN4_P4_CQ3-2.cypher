// SpectraCQ RAN4_P4_CQ3-2 (RAN4, phase 4) -- CQ3_CRPack
// Question: Which CR packs contain CRs for NR_newRAT work items? (work-item packaging trace).
// Gold: 10 rows, primary column "crPackId"

MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS 'NR_newRAT' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC LIMIT 10
