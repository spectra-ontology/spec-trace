// SpectraCQ P4_CQ3-2 — CQ3_CRPack분석
// Question (English): Return the CR Packs that bundle CRs from Work Item NR_newRAT-Core toward TSG approval.
// Schema area: classes=['CR', 'CRPack', 'WorkItem'], rels=['BELONGS_TO_CR_PACK', 'RELATED_TO']

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_newRAT-Core'}) MATCH (cr)-[:BELONGS_TO_CR_PACK]->(pack:CRPack) RETURN wi.workItemCode, pack.crPackId, pack.tsgMeeting, count(cr) AS crCount ORDER BY pack.tsgMeeting DESC, crCount DESC LIMIT 15
