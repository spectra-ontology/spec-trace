// SpectraCQ P4_CQ4-4 — CQ4_연계분석
// Question (English): Return the cross-spec impact distribution of recent CompanyE-submitted CRs (most-cross-spec company, latest first).
// Schema area: classes=['CR', 'Company', 'Spec'], rels=['AFFECTS_CORE_SPEC', 'SUBMITTED_BY']

MATCH (cr:CR)-[:SUBMITTED_BY]->(co:Company {companyName: 'CompanyE'}) MATCH (cr)-[:AFFECTS_CORE_SPEC|AFFECTS_TEST_SPEC|AFFECTS_OM_SPEC]->(sp:Spec) RETURN co.companyName, cr.tdocNumber, collect(DISTINCT sp.specNumber) AS affectedSpecs ORDER BY cr.tdocNumber DESC LIMIT 15
