# Team B — Case Source

**Team B** is a protocol-software team that implements the communication protocol stack
— NAS, RRC, MAC, and the other 3GPP protocol layers — running on the cellular modem. It
operates in a separate management line from Teams A and C.

The questions in this folder are real questions raised by the team's engineers during
protocol implementation and conformance work, answered by SPECTRA. Each case directory
contains the question (`00_original_question.md`, translated from Korean) and the cited
SPECTRA answer (`01_spectra_answer.md`). To protect individual contributors, no case is
attributed to a named organizational unit.

| Case | Topic |
|---|---|
| `case_001_pdu_release_reject_cause43` | Registration request after PDU session release reject with 5GSM cause #43 |
| `case_002_lte_neighcells_crs_assumptions` | LTE neighbour-cell CRS assumptions |
| `case_003_emergency_dereg_test_11_4_1` | Emergency services and de-registration, conformance test 11.4.1 |
| `case_004_pc1_5_max_output_power_clause_removed_v17` | PC1.5 maximum output power clause removed in v17 |
| `case_005_rel18_dci_waveform_switch_dci_0_1_bit_size` | Rel-18 dynamic waveform switching and DCI 0_1 bit-size derivation |
| `case_006_ntn_t430_epochtime_sfn_wraparound` | NTN T430 epoch time and SFN wraparound |
| `case_007_single_port_vs_single_antenna_port_terminology_38101` | "Single port" vs "single antenna port" terminology in TS 38.101 |
| `case_008_hplmn_search_full_vs_stored_frequency_scan` | HPLMN search: full band scan vs stored frequency scan |
| `case_009_ntn_referencelocation_degreeslongitude_asn1_vs_2scomplement` | NTN referenceLocation degreesLongitude: ASN.1 value range vs 2's-complement encoding |
