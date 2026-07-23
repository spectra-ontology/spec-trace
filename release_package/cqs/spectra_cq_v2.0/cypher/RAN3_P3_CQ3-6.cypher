// SpectraCQ RAN3_P3_CQ3-6 (RAN3, phase 3) -- CQ3_CR
// Question: Return the specs that Huawei's CRs modify (company change footprint).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
