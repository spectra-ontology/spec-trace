// SpectraCQ RAN3_P3_P3-S8-CQ01 (RAN3, phase 3) -- CQ_Step8_EntityCount
// Question: Return the item-level node count for each of the five entity classes RRCParameter, CapabilityItem, Procedure, PerformanceRequirement, and ConformanceTest (entity-layer inventory).
// Gold: 2 rows, primary column "class"

MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest'])   AND n.granularity = 'item' RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        count(n) AS items ORDER BY items DESC
