// SpectraCQ RAN2_P4_CQ2-4 (RAN2, phase 4) -- CQ2_CrossSpec
// Question: Return the top 10 CRs by cross-spec impact count (widest-reaching CRs).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
