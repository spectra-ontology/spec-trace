// SpectraCQ RAN5_P4_CQ3-3 (RAN5, phase 4) -- CQ3_CRPack
// Question: List the ten largest CR packs by CR count (pack overview).
// Gold: 10 rows, primary column "crPackId"

MATCH (pack:CRPack)-[:HAS_CR]->(cr:CR) RETURN pack.crPackId AS crPackId, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
