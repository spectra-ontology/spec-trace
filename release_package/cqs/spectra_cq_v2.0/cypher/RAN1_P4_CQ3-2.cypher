// SpectraCQ RAN1_P4_CQ3-2 (RAN1, phase 4) -- CQ3_CRPack
// Question: Into which CR packs were the CRs of Work Item NR_newRAT-Core (initial NR spec) bundled for TSG submission?
// Gold: 15 rows, primary column "wi.workItemCode"

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(cr) AS crCount ORDER BY pack.tsgMeeting DESC, crCount DESC LIMIT 15
