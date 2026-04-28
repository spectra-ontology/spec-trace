// SpectraCQ P4_CQ4-2 — CQ4_연계분석
// Question (English): Return the change-reason and change-summary of CRs approved by Resolution AGR-115-7.1-004.
// Schema area: classes=['CR', 'Resolution'], rels=['REFERENCES']

MATCH (res:Resolution {resolutionId: 'AGR-115-7.1-004'})-[:REFERENCES]->(cr:CR) RETURN res.resolutionId, cr.tdocNumber, cr.reasonForChange, cr.summaryOfChange ORDER BY cr.tdocNumber ASC
