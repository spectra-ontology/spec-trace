// SpectraCQ RAN2_P4_CQ2-3 (RAN2, phase 4) -- CQ2_CrossSpec
// Question: List the CRs that name spec 38.212 as an affected spec (incoming impact).
// Gold: 8 rows, primary column "tdocNumber"

MATCH (s:Spec {specNumber: '38.212'})<-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]-(c:CR) RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
