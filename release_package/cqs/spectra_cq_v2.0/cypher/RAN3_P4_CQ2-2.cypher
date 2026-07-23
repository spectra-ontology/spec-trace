// SpectraCQ RAN3_P4_CQ2-2 (RAN3, phase 4) -- CQ2_CrossSpec
// Question: List CRs modifying spec 38.423 that also affect other specs (ripple-effect detection).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.423'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
