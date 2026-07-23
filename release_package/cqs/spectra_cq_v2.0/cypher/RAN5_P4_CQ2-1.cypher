// SpectraCQ RAN5_P4_CQ2-1 (RAN5, phase 4) -- CQ2_CrossSpec
// Question: List the other specs affected by CR R5-255419 (cross-spec impact).
// Gold: 1 rows, primary column "c.tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(s:Spec) WHERE c.tdocNumber = 'R5-255419' RETURN c.tdocNumber, type(r) AS relType, s.specNumber ORDER BY s.specNumber
