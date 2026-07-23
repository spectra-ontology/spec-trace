// SpectraCQ RAN5_P3_P3-S8-CQ06 (RAN5, phase 3) -- CQ_Step8_CoreIE_Baseline
// Question: Do the baseline IEs (CodebookConfig-r16, LTM-Config-r18, BeamFailureRecoveryConfig, TCI-State) exist as RRCParameter nodes? (baseline presence check)
// Gold: 6 rows, primary column "expected"

UNWIND ['CodebookConfig-r16','LTM-Config-r18','BeamFailureRecoveryConfig','TCI-State','TCI-UL-State-r17','RadioLinkMonitoringConfig'] AS expected OPTIONAL MATCH (ie:RRCParameter {ieName: expected}) RETURN expected, ie IS NOT NULL AS found, ie.specNumber AS spec, ie.release AS release
