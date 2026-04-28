// SpectraCQ P4_CQ2-4 — CQ2_CrossSpec영향
// Question (English): Return the top-10 CRs by cross-spec impact span and the affected-spec list per CR.
// Schema area: classes=['CR', 'Spec'], rels=['AFFECTS_CORE_SPEC']

MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, count(DISTINCT sp) AS affectedSpecCount, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY affectedSpecCount DESC, cr.tdocNumber ASC LIMIT 10
