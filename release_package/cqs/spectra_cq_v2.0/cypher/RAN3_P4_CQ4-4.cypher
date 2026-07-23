// SpectraCQ RAN3_P4_CQ4-4 (RAN3, phase 4) -- CQ4
// Question: List the specs affected by Samsung's CRs (company cross-spec footprint).
// Gold: 10 rows, primary column "spec"

MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
