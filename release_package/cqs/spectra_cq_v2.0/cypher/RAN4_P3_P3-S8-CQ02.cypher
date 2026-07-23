// SpectraCQ RAN4_P3_P3-S8-CQ02 (RAN4, phase 3) -- CQ_Step8_DefinedInSection
// Question: Are all item-level entity nodes linked to a Section via definedInSection? (grounding-coverage check).
// Gold: 2 rows, primary column "class"

MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' WITH n, exists((n)-[:definedInSection]->(:Section)) AS linked RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS total,        sum(CASE WHEN linked THEN 1 ELSE 0 END) AS linked,        round(100.0 * sum(CASE WHEN linked THEN 1 ELSE 0 END) / count(n), 1) AS link_pct
