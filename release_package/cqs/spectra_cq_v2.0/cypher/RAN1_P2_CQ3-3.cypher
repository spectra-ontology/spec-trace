// SpectraCQ RAN1_P2_CQ3-3 (RAN1, phase 2) -- CQ3
// Question: Which companies contributed most to resolutions under NR MIMO (Agenda 7.1)? Top 10.
// Gold: 10 rows, primary column "c.companyName"

MATCH (a:Agreement)-[:REFERENCES]->(t:Tdoc)-[:SUBMITTED_BY]->(c:Company), (a)-[:RESOLUTION_BELONGS_TO]->(ai:AgendaItem) WHERE ai.agendaNumber STARTS WITH '7.1' RETURN c.companyName, count(DISTINCT a) AS contributionCount ORDER BY contributionCount DESC LIMIT 10
