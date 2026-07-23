// SpectraCQ RAN5_P4_CQ3-1 (RAN5, phase 4) -- CQ3_CRPack
// Question: List the CRs in a CR pack with their change summaries (pack contents).
// Gold: 10 rows, primary column "crPackId"

MATCH (pack:CRPack)-[:HAS_CR]->(c:CR) WITH pack, c ORDER BY c.tdocNumber LIMIT 10 RETURN pack.crPackId AS crPackId, c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary
