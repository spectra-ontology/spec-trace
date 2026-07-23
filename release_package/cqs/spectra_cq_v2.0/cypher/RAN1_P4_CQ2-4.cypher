// SpectraCQ RAN1_P4_CQ2-4 (RAN1, phase 4) -- CQ2_CrossSpec
// Question: Which 10 CRs have the widest cross-spec reach, and which specs does each affect?
// Gold: 10 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, count(DISTINCT sp) AS affectedSpecCount, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC, cr.tdocNumber ASC LIMIT 10
