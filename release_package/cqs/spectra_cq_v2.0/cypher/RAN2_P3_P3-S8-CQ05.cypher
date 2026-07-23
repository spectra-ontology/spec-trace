// SpectraCQ RAN2_P3_P3-S8-CQ05 (RAN2, phase 3) -- CQ_Step8_GranularityDump
// Question: Return the granularity-property distribution across the five entity classes (item-level v3.0 vs section-level legacy).
// Gold: 3 rows, primary column "class"

MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
