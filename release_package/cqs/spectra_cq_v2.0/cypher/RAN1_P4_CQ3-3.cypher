// SpectraCQ RAN1_P4_CQ3-3 (RAN1, phase 4) -- CQ3_CRPack
// Question: List the CR packs submitted to plenary RAN#109 and the CR count in each.
// Gold: 10 rows, primary column "pack.tsgMeeting"

MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) WHERE pack.tsgMeeting = 'RAN#109' RETURN pack.tsgMeeting, pack.crPackId, count(cr) AS crCount ORDER BY crCount DESC
