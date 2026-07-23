// SpectraCQ RAN4_P4_CQ2-4 (RAN4, phase 4) -- CQ2_CrossSpec
// Question: List the top 10 CRs by number of cross-spec impacts (widest-reaching changes).
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
