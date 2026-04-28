// SpectraCQ P4_CQ2-1 — CQ2_CrossSpec영향
// Question (English): Return the 5 specs affected by CR R1-2599971 along with each impact-relation type (Core/Test/OM).
// Schema area: classes=['CR', 'Spec'], rels=[]

MATCH (cr:CR {tdocNumber: 'R1-2599971'})-[r:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN cr.tdocNumber, sp.specNumber, type(r) AS relationType ORDER BY sp.specNumber ASC
