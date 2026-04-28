// SpectraCQ P4_CQ3-1 — CQ3_CRPack분석
// Question (English): Return CRs in CRPack RP-252634 (latest RAN#109) and each CR's change summary.
// Schema area: classes=['CR', 'CRPack'], rels=['HAS_CR']

MATCH (pack:CRPack {crPackId: 'RP-252634'})-[:HAS_CR]->(cr:CR) RETURN pack.crPackId, pack.tsgMeeting, cr.tdocNumber, cr.summaryOfChange ORDER BY cr.tdocNumber ASC
