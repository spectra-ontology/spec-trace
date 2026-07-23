// SpectraCQ RAN5_P4_CQ3-2 (RAN5, phase 4) -- CQ3_CRPack
// Question: Which CR packs contain CRs for the 5GS_NR_LTE-UEConTest work items? (work-item pack lookup)
// Gold: 10 rows, primary column "crPackId"

MATCH (c:CR)-[:RELATED_TO]->(w:WorkItem) WHERE w.workItemCode CONTAINS '5GS_NR_LTE-UEConTest' WITH c MATCH (c)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN DISTINCT pack.crPackId AS crPackId, pack.tsgMeeting AS tsgMeeting ORDER BY pack.tsgMeeting DESC, pack.crPackId LIMIT 10
