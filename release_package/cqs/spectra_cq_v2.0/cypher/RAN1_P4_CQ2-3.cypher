// SpectraCQ RAN1_P4_CQ2-3 (RAN1, phase 4) -- CQ2_CrossSpec
// Question: How many CRs list TS 38.214 as a cross-spec impact target, and which are representative?
// Gold: 1 rows, primary column "sp.specNumber"

MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec {specNumber: '38.214'}) WITH sp, collect(cr.tdocNumber) AS crList, count(cr) AS crCount RETURN sp.specNumber, crCount, crList[..10] AS sampleCRs
