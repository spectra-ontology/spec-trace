// SpectraCQ RAN5_P4_CQ2-4 (RAN5, phase 4) -- CQ2_CrossSpec
// Question: Which ten CRs affect the most other specs? (broadest-impact ranking)
// Gold: 10 rows, primary column "tdocNumber"

MATCH (c:CR)-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->() WITH c, count(r) AS cnt ORDER BY cnt DESC, c.tdocNumber LIMIT 10 RETURN c.tdocNumber AS tdocNumber, cnt
