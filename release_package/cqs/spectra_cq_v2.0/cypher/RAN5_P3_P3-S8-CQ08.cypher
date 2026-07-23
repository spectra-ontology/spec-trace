// SpectraCQ RAN5_P3_P3-S8-CQ08 (RAN5, phase 3) -- CQ_Step8_FeatureCatalogParity
// Question: Are all 22 features from the feature catalog loaded as Feature nodes? (feature-catalog parity)
// Gold: 1 rows, primary column "feature_count"

MATCH (f:Feature) RETURN count(f) AS feature_count, collect(f.featureId)[..30] AS feature_ids ORDER BY feature_count DESC
