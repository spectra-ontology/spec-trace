// SpectraCQ RAN1_P2_CQ4-3 (RAN1, phase 2) -- CQ4
// Question: Which companies handled the most FL summaries? Top 10 (technical-leadership ranking).
// Gold: 10 rows, primary column "c.companyName"

MATCH (t:Tdoc)-[:MODERATED_BY]->(c:Company)
WHERE t.summaryType = 'FL'
RETURN c.companyName, count(t) AS flCount ORDER BY flCount DESC, c.companyName LIMIT 10
