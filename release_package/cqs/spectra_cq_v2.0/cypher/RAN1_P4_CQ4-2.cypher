// SpectraCQ RAN1_P4_CQ4-2 (RAN1, phase 4) -- CQ4
// Question: For the CRs approved by resolution AGR-115-7.1-004, give the reason-for-change and summary-of-change.
// Gold: 5 rows, primary column "res.resolutionId"

MATCH (res:Resolution {resolutionId: 'AGR-115-7.1-004'})-[:REFERENCES]->(cr:CR) RETURN res.resolutionId, cr.tdocNumber, cr.reasonForChange, cr.summaryOfChange ORDER BY cr.tdocNumber ASC
