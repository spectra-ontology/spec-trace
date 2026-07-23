// SpectraCQ RAN2_P3_P3-S8-CQ07 (RAN2, phase 3) -- CQ_Step8_LTM_Capabilities
// Question: Are the 28 LTM capability items loaded as CapabilityItem nodes (LTM baseline check)?
// Gold: 1 rows, primary column "ltm_cap_count"

MATCH (cap:CapabilityItem) WHERE cap.capabilityItemName STARTS WITH 'ltm-' AND cap.granularity = 'item' RETURN count(cap) AS ltm_cap_count, collect(cap.capabilityItemName)[..10] AS sample
