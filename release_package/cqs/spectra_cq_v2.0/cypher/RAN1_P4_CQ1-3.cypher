// SpectraCQ RAN1_P4_CQ1-3 (RAN1, phase 4) -- CQ1_CR
// Question: What happens if the CRs under Work Item NR_LPWUS-Core (Rel-19 LP-WUS/WUR) are not approved? (consequences-if-not-approved)
// Gold: 14 rows, primary column "cr.tdocNumber"

MATCH (cr:CR)-[:RELATED_TO]->(wi:WorkItem {workItemCode: 'NR_LPWUS-Core'}) WHERE cr.consequencesIfNotApproved IS NOT NULL RETURN cr.tdocNumber, cr.consequencesIfNotApproved ORDER BY cr.tdocNumber DESC
