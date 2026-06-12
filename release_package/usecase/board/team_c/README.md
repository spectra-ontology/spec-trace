# Team C — Case Source

**Team C** is a 3GPP RAN standardization team whose delegates contribute to the RAN1
(physical layer) and RAN2 (RRC/MAC) working groups. It operates in a separate management
line from Teams A and B.

The questions in this folder are real questions raised by the team's standardization
engineers during 3GPP contribution and specification work, answered by SPECTRA. Cases
are grouped by the working group the question concerns: `RAN1_case/` (PHY) and
`RAN2_case/` (RRC/MAC). Each case directory contains the question
(`00_original_question.md`, translated from Korean) and the cited SPECTRA answer
(`01_spectra_answer.md`). To protect individual contributors, no case is attributed to a
named organizational unit.

## RAN1 (PHY) cases

| Case | Topic |
|---|---|
| `RAN1_case/case_001_srs_pusch_pucch_priority` | SRS vs PUSCH/PUCCH collision handling and transmission priority |
| `RAN1_case/case_002_uci_pusch_etype2_csi_part2_omission` | UCI on PUSCH: enhanced Type-II CSI Part 2 omission rules |
| `RAN1_case/case_003_dci_duplicate_ul_scheduling_cancel` | Duplicate DCI uplink scheduling and cancellation behaviour |
| `RAN1_case/case_004_subband_pmi_layer_indicator_uci_bit` | Subband PMI / layer-indicator UCI bit-width derivation |

## RAN2 (RRC/MAC) cases

| Case | Topic |
|---|---|
| `RAN2_case/case_001_neighbor_cell_pbch_decoding_rrm_handover` | Neighbour-cell PBCH decoding for RRM measurement and handover |
| `RAN2_case/case_002_rrm_pbch_decode_intra_inter_ssb_csirs` | RRM PBCH decoding across intra/inter-frequency SSB and CSI-RS |
| `RAN2_case/case_003_2step_cfra_msga_crnti_mac_ce_handover` | 2-step CFRA MsgA C-RNTI / MAC CE handling at handover |
| `RAN2_case/case_004_rach_config_ssb_perrach_absent_default_handover` | RACH config: ssb-perRACH-Occasion absent default at handover |
| `RAN2_case/case_005_phr_p_field_mpe_reporting_pcmax` | PHR P-field, MPE reporting, and PCMAX interaction |
| `RAN2_case/case_006_endc_phr_real_virtual_pcell_type1_ph` | EN-DC PHR: real vs virtual PCell Type-1 power headroom |
| `RAN2_case/case_007_mbs_multicast_ptp_rlc_architecture` | MBS multicast PTP/PTM RLC architecture |
| `RAN2_case/case_008_bwp_switching_random_access_pseudocode_spcell_scell` | BWP switching during random access on SpCell/SCell |
