// SpectraCQ RAN5_P3_CQ4-3 (RAN5, phase 3) -- CQ4_Resolution
// Question: Per meeting, which RAN5 specs do approved CRs modify? (meeting-level spec impact)
// Gold: 10 rows, primary column "meeting"

MATCH (res:Conclusion)-[:MADE_AT]->(m:Meeting), (res)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(sp:Spec) WHERE sp.specNumber STARTS WITH '38.5' WITH m.canonicalMeetingNumber AS meeting, sp.specNumber AS spec, count(DISTINCT t) AS crCount RETURN meeting, spec, crCount ORDER BY crCount DESC, meeting, spec LIMIT 10
