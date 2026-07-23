// SpectraCQ RAN4_P4_CQ3-3 (RAN4, phase 4) -- CQ3_CRPack
// Question: List the CR packs submitted to TSG meeting RAN#102 (plenary submission overview).
// Gold: 10 rows, primary column "crPackId"

MATCH (pack:CRPack {tsgMeeting: 'RAN#102'}) RETURN pack.crPackId AS crPackId ORDER BY pack.crPackId LIMIT 10
