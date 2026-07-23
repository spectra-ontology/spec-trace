// SpectraCQ RAN2_P2_CQ1-10 (RAN2, phase 2) -- CQ1_Resolution
// Question: Return resolution counts by type at meeting RAN2#132 (meeting decision mix).
// Gold: 2 rows, primary column "type"

MATCH (r:Resolution)-[:MADE_AT]->(m:Meeting {canonicalMeetingNumber: 'RAN2#132'}) RETURN CASE WHEN r:Agreement THEN 'Agreement' WHEN r:Conclusion THEN 'Conclusion' WHEN r:WorkingAssumption THEN 'WorkingAssumption' END AS type, count(r) AS cnt ORDER BY cnt DESC
