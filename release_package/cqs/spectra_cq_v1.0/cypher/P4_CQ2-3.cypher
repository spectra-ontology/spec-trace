// SpectraCQ P4_CQ2-3 — CQ2_CrossSpec영향
// Question (English): Return the total count and representative numbers of CRs that mark TS 38.214 as a cross-spec impact target.
// Schema area: classes=['CR', 'Spec'], rels=['AFFECTS_CORE_SPEC']

MATCH (cr:CR)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec {specNumber: '38.214'}) WITH sp, collect(cr.tdocNumber) AS crList, count(cr) AS crCount RETURN sp.specNumber, crCount, crList[..10] AS sampleCRs
