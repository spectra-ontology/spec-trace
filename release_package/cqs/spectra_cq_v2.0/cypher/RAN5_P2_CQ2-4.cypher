// SpectraCQ RAN5_P2_CQ2-4 (RAN5, phase 2) -- CQ2_Tdoc-Resolution
// Question: Which specs does each referenced TDoc end up modifying? (document-to-spec impact)
// Gold: 10 rows, primary column "tdoc"

MATCH (r:Resolution)-[:REFERENCES]->(t:Tdoc)-[:MODIFIES]->(s:Spec) WITH t.tdocNumber AS tdoc, collect(DISTINCT s.specNumber) AS specs, count(DISTINCT s) AS spec_count ORDER BY spec_count DESC, tdoc LIMIT 10 RETURN tdoc, spec_count, specs[..5] AS sample_specs
