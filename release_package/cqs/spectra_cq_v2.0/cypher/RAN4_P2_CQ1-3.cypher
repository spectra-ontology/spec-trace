// SpectraCQ RAN4_P2_CQ1-3 (RAN4, phase 2) -- CQ1_Resolution
// Question: Which meetings recorded working assumptions? (locating open assumptions).
// Gold: 3 rows, primary column "m.canonicalMeetingNumber"

MATCH (w:WorkingAssumption)-[:MADE_AT]->(m:Meeting) RETURN m.canonicalMeetingNumber, count(w) AS cnt ORDER BY cnt DESC LIMIT 15
