// SpectraCQ RAN2_P3_P3-S8-CQ04 (RAN2, phase 3) -- CQ_Step8_FeatureDisjoint
// Question: Do the disjointWith relations among features (LTM, CHO, CPC, CPAC, etc.) match feature_catalog.disjoint_feature_groups (consistency check)?
// Gold: 6 rows, primary column "a"

MATCH (a:Feature)-[:disjointWith]->(b:Feature) WHERE a.name < b.name RETURN a.name AS a, b.name AS b ORDER BY a, b
