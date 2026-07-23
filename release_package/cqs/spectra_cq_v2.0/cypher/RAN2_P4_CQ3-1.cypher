// SpectraCQ RAN2_P4_CQ3-1 (RAN2, phase 4) -- CQ3_CRPack
// Question: List the CRs in CR pack RP-253714 with their change summaries (pack contents).
// Gold: 5 rows, primary column "tdocNumber"

MATCH (pack:CRPack {crPackId: 'RP-253714'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber DESC LIMIT 10
