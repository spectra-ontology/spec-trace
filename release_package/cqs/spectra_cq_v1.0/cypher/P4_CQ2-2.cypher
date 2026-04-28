// SpectraCQ P4_CQ2-2 — CQ2_CrossSpec영향
// Question (English): Return the spec most often subject to cross-spec impact from CRs that modify TS 38.214, with CR counts.
// Schema area: classes=['CR', 'Spec'], rels=['AFFECTS_CORE_SPEC', 'MODIFIES']

MATCH (cr:CR)-[:MODIFIES]->(mainSpec:Spec {specNumber: '38.214'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(otherSpec:Spec) WHERE mainSpec <> otherSpec RETURN mainSpec.specNumber AS modifiedSpec, otherSpec.specNumber AS affectedSpec, count(DISTINCT cr) AS crCount ORDER BY crCount DESC
