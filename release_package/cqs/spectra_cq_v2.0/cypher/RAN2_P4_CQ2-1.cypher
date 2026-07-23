// SpectraCQ RAN2_P4_CQ2-1 (RAN2, phase 4) -- CQ2_CrossSpec
// Question: List the other specs affected by CR R2-2001766 (cross-spec impact).
// Gold: 4 rows, primary column "relType"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R2-2001766' RETURN type(r) AS relType, s.specNumber AS spec
