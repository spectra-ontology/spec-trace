// SpectraCQ RAN4_P3_CQ3-6 (RAN4, phase 3) -- CQ3_CR
// Question: How many CRs did Huawei submit against spec 38.133? (per-company change count).
// Gold: 1 rows, primary column "crCount"

MATCH (cr:CR)-[:MODIFIES]->(sp:Spec {specNumber: '38.133'}), (cr)-[:SUBMITTED_BY]->(c:Company {companyName: 'Huawei'}) RETURN count(cr) AS crCount
