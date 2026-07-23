// SpectraCQ RAN5_P2_CQ2-1 (RAN5, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which TDocs are referenced by two or more resolutions? (frequently-cited documents)
// Gold: 7 rows, primary column "tdoc"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc) WITH t.tdocNumber AS tdoc, count(r) AS ref_count WHERE ref_count >= 2 RETURN tdoc, ref_count ORDER BY ref_count DESC LIMIT 10
