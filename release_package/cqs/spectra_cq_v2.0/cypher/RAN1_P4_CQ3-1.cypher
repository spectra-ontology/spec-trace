// SpectraCQ RAN1_P4_CQ3-1 (RAN1, phase 4) -- CQ3_CRPack
// Question: List the CRs in CR pack RP-252634 (submitted to the latest plenary RAN#109), with each CR's summary-of-change.
// Gold: 9 rows, primary column "pack.crPackId"

MATCH (pack:CRPack {crPackId: 'RP-252634'})-[:HAS_CR]->(cr:CR) RETURN pack.crPackId, pack.tsgMeeting, cr.tdocNumber, cr.summaryOfChange ORDER BY cr.tdocNumber ASC
