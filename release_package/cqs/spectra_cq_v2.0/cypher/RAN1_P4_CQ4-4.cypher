// SpectraCQ RAN1_P4_CQ4-4 (RAN1, phase 4) -- CQ4
// Question: For Samsung's recent CRs with cross-spec impact, what is the distribution of affected specs? (latest first)
// Gold: 15 rows, primary column "co.companyName"

MATCH (cr:CR)-[:SUBMITTED_BY]->(co:Company {companyName: 'Samsung'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN co.companyName, cr.tdocNumber, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY cr.tdocNumber DESC LIMIT 15
