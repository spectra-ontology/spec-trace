// SpectraCQ RAN1_P3_P3-S8-CQ04 (RAN1, phase 3) -- CQ_Step8_FeatureDisjoint
// Question: Do the disjointWith relations between Features (LTM, CHO, CPC, CPAC, etc.) match the feature catalog's disjoint groups? (consistency check)
// Gold: 6 rows, primary column "a"

MATCH (a:Feature)-[:disjointWith]->(b:Feature) WHERE a.name < b.name RETURN a.name AS a, b.name AS b ORDER BY a, b
