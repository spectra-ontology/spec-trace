// SpectraCQ RAN5_P2_CQ1-3 (RAN5, phase 2) -- CQ1_Resolution
// Question: How many resolutions relate to each release? (release-outcome breakdown)
// Gold: 7 rows, primary column "release"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:TARGET_RELEASE]->(rel:Release) WHERE rel.releaseName STARTS WITH 'Rel-' WITH rel.releaseName AS release, count(DISTINCT r) AS cnt ORDER BY cnt DESC LIMIT 10 RETURN release, cnt
