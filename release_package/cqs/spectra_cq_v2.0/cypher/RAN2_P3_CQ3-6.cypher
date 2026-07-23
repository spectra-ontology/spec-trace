// SpectraCQ RAN2_P3_CQ3-6 (RAN2, phase 3) -- CQ3_CR
// Question: List the specs modified by Huawei's CRs (vendor footprint).
// Gold: 10 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}), (cr)-[:MODIFIES]->(sp:Spec) RETURN DISTINCT sp.specNumber, count(cr) AS crs ORDER BY crs DESC LIMIT 10
