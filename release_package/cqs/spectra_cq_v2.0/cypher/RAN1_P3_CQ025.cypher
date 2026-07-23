// SpectraCQ RAN1_P3_CQ025 (RAN1, phase 3) -- Resolution_TS
// Question: Summarize the number of agreements per TS (which spec sees the most consensus).
// Gold: 6 rows, primary column "sp.specNumber"

MATCH (agr:Agreement)-[:REFERENCES]->(cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.201','38.202','38.211','38.212','38.213','38.214','38.215','38.291'] RETURN sp.specNumber, count(DISTINCT agr) AS agrCount ORDER BY agrCount DESC
