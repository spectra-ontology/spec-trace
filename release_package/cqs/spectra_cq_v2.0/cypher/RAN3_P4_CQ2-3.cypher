// SpectraCQ RAN3_P4_CQ2-3 (RAN3, phase 4) -- CQ2_CrossSpec
// Question: List CRs that name spec 38.473 as an affected spec (incoming cross-spec impact).
// Gold: 10 rows, primary column "c.tdocNumber"

MATCH (s:Spec {specNumber: '38.473'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber, c.summaryOfChange ORDER BY c.tdocNumber DESC LIMIT 10
