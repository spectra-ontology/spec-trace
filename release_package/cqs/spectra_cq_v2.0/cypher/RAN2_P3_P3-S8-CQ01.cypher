// SpectraCQ RAN2_P3_P3-S8-CQ01 (RAN2, phase 3) -- CQ_Step8_EntityCount
// Question: Return the item-level node counts for the five entity classes RRCParameter, CapabilityItem, Procedure, PerformanceRequirement, and ConformanceTest (entity-layer census).
// Gold: 3 rows, primary column "class"

MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS items ORDER BY items DESC
