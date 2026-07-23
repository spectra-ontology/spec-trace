// SpectraCQ RAN5_P4_CQ4-4 (RAN5, phase 4) -- CQ4
// Question: Which other specs do Samsung's CRs affect? (company cross-spec impact)
// Gold: 10 rows, primary column "spec"

MATCH (c:CR)-[:SUBMITTED_BY]->(comp:Company) WHERE comp.companyName CONTAINS 'Samsung' WITH c MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) RETURN DISTINCT s.specNumber AS spec ORDER BY spec LIMIT 10
