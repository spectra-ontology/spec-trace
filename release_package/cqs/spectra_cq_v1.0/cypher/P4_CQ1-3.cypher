// SpectraCQ P4_CQ1-3 — CQ1_CR변경근거
// Question (English): Return the consequences-if-not-approved for CRs in Work Item NR_LPWUS-Core (Rel-19 LP-WUS/WUR).
// Schema area: classes=['CR', 'WorkItem'], rels=['RELATED_TO']

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved ORDER BY cr.tdocNumber DESC
