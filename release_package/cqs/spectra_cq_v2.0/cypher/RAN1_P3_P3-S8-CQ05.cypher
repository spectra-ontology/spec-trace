// SpectraCQ RAN1_P3_P3-S8-CQ05 (RAN1, phase 3) -- CQ_Step8_GranularityDump
// Question: What is the granularity-property distribution across the five entity classes? (item-level vs. section-level)
// Gold: 1 rows, primary column "class"

MATCH (n) WHERE any(l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']) RETURN [l IN labels(n) WHERE l IN ['RRCParameter','CapabilityItem','Procedure','PerformanceRequirement','ConformanceTest']][0] AS class,        coalesce(n.granularity, '<unset>') AS granularity,        count(n) AS c ORDER BY class, granularity
