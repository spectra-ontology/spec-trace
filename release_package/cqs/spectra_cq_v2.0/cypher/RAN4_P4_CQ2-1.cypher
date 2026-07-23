// SpectraCQ RAN4_P4_CQ2-1 (RAN4, phase 4) -- CQ2_CrossSpec
// Question: List the other specs affected by CR R4-2207489 (cross-spec impact assessment).
// Gold: 2 rows, primary column "c.tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R4-2207489' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
