// SpectraCQ RAN1_P3_CQ040 (RAN1, phase 3) -- 
// Question: Compare CR counts against agreement counts per TS (which spec changes most relative to consensus).
// Gold: 5 rows, primary column "ts"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215'] WITH sp.specNumber AS ts, count(cr) AS crCnt OPTIONAL MATCH (agr:Agreement)-[:REFERENCES]->(cr2:CR)-[:MODIFIES]->(sp2:Spec) WHERE sp2.specNumber = ts RETURN ts, crCnt, count(DISTINCT agr) AS agrCnt ORDER BY crCnt DESC
