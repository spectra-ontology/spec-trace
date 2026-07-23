// SpectraCQ RAN4_P4_CQ3-1 (RAN4, phase 4) -- CQ3_CRPack
// Question: List the CRs in CR pack RP-233366 with their change summaries (CR-pack contents review).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (pack:CRPack {crPackId: 'RP-233366'})-[:HAS_CR]->(c:CR) RETURN c.tdocNumber AS tdocNumber, c.summaryOfChange AS summary ORDER BY c.tdocNumber LIMIT 10
