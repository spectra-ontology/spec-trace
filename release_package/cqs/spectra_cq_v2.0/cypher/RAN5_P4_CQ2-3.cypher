// SpectraCQ RAN5_P4_CQ2-3 (RAN5, phase 4) -- CQ2_CrossSpec
// Question: List the CRs that flag TS 38.533 as an affected spec (incoming impact).
// Gold: 10 rows, primary column "c.tdocNumber"

MATCH (s:Spec {specNumber: '38.533'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
