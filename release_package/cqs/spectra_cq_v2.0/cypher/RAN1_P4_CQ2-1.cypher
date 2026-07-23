// SpectraCQ RAN1_P4_CQ2-1 (RAN1, phase 4) -- CQ2_CrossSpec
// Question: List the five specs CR R1-2504971 affects and the impact type (Core/Test/OM) for each.
// Gold: 5 rows, primary column "cr.tdocNumber"

MATCH (cr:CR {tdocNumber: 'R1-2504971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, sp.specNumber, type(r) AS relationType ORDER BY sp.specNumber ASC
