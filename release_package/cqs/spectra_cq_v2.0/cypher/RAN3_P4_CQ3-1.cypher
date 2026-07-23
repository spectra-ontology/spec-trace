// SpectraCQ RAN3_P4_CQ3-1 (RAN3, phase 4) -- CQ3_CRPack
// Question: List the CRs in CR pack RP-241113 with their change summaries (pack-content review).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (pack:CRPack {crPackId: 'RP-241113'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
