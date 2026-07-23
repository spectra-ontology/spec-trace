// SpectraCQ RAN5_P4_CQ2-2 (RAN5, phase 4) -- CQ2_CrossSpec
// Question: Which CRs modifying TS 38.521-1 also affect other specs? (ripple-effect screening)
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.521-1'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
