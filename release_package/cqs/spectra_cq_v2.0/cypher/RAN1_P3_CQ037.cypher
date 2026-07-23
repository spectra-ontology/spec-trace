// SpectraCQ RAN1_P3_CQ037 (RAN1, phase 3) -- 
// Question: Rank companies by total CRs submitted across the eight TSs (who the major players are).
// Gold: 15 rows, primary column "co.companyName"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber IN ['38.211','38.212','38.213','38.214','38.215','38.201','38.202','38.291'] MATCH (cr)-[:SUBMITTED_BY]->(co:Company) RETURN co.companyName, count(cr) AS crCount ORDER BY crCount DESC LIMIT 15
