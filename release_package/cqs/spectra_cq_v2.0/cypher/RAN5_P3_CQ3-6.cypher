// SpectraCQ RAN5_P3_CQ3-6 (RAN5, phase 3) -- CQ3_CR
// Question: Which RAN5 specs does each company modify via CRs? (company spec impact)
// Gold: 10 rows, primary column "c.companyName"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company), (cr)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' RETURN c.companyName, sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 10
