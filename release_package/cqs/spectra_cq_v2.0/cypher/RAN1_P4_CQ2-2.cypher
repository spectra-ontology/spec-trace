// SpectraCQ RAN1_P4_CQ2-2 (RAN1, phase 4) -- CQ2_CrossSpec
// Question: Which other specs do CRs modifying TS 38.214 most often ripple into, and how many CRs each?
// Gold: 10 rows, primary column "modifiedSpec"

MATCH (cr:CR)-[:MODIFIES]->(mainSpec:Spec {specNumber: '38.214'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(otherSpec:Spec) WHERE mainSpec <> otherSpec RETURN mainSpec.specNumber AS modifiedSpec, otherSpec.specNumber AS affectedSpec, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
