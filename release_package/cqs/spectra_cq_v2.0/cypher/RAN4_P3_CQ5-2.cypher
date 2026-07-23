// SpectraCQ RAN4_P3_CQ5-2 (RAN4, phase 3) -- CQ5
// Question: List Huawei's top 5 specs by CR contributions (a company's change focus).
// Gold: 5 rows, primary column "sp.specNumber"

MATCH (c:Company {companyName: 'Huawei'})<-[:SUBMITTED_BY]-(cr:CR)-[:MODIFIES]->(sp:Spec) RETURN sp.specNumber, count(cr) AS crCount ORDER BY crCount DESC LIMIT 5
