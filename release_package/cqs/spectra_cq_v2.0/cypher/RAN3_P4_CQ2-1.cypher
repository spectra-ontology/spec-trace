// SpectraCQ RAN3_P4_CQ2-1 (RAN3, phase 4) -- CQ2_CrossSpec
// Question: List the other specs affected by CR R3-244680 (cross-spec impact).
// Gold: 1 rows, primary column "c.tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R3-244680' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
