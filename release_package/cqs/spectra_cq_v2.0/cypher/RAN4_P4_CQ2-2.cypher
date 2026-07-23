// SpectraCQ RAN4_P4_CQ2-2 (RAN4, phase 4) -- CQ2_CrossSpec
// Question: Which CRs modifying spec 38.133 also affect other specs? (ripple-effect screening).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[:MODIFIES]->(s:Spec {specNumber: '38.133'}) WHERE EXISTS { MATCH (c)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() } RETURN c.tdocNumber AS tdocNumber ORDER BY c.tdocNumber DESC LIMIT 10
