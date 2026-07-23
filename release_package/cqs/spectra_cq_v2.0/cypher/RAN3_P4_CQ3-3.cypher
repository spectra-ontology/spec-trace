// SpectraCQ RAN3_P4_CQ3-3 (RAN3, phase 4) -- CQ3_CRPack
// Question: List the CR packs submitted to TSG meeting RAN#110 (plenary submission review).
// Gold: 10 rows, primary column "crPackId"

MATCH (pack:CRPack {tsgMeeting: 'RAN#110'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
