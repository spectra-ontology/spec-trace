# LTM (L1/L2 Triggered Mobility) Rel-18 — A v5 Standardization Analysis

> Disjoint-feature aware + capability_enums verbatim. Generated 2026-05-19 to address Q4 reviewer feedback D-A (CPAC false positive) and D-B (38.306 §4.2.7.2/4 LTM cap items missing).

## Table of Contents

- §0 Evidence Provenance
- §1 Motivation
- §2 38.300 — Architecture (Stage-2 location)
- §3 38.213 / 38.214 — PHY / CSI Procedures
- §4 38.321 — MAC CE for LTM Cell Switch
- §5 38.331 — LTM RRC IE Family (19 IEs enumerated)
- §6 38.306 — UE Capability (28 ltm-* items verbatim, Rule 26)
- §7 38.133 — RAN4 Mobility Delay (cross-WG)
- §8 Disjoint Features — LTM ⊥ CHO ⊥ CPC ⊥ CPAC (Rule 25)
- §9 Cross-Document Linkages
- §10 Coverage and Limitations
- §11 Summary

---

## 0. Evidence Provenance

This report is grounded in `logs/cross-phase/usecase/q4_retrieval_log_v3_dryrun.json` (regenerated 2026-05-19 with `capability_enums.items_extracted` field, system_prompt Rule 25/26 active, feature_catalog v1.2-2026-05-19).

- **v3 catalog enum**: 19 LTM-* IEs from `ran2_ts_asn1_chunks`; 209 section hits across 38.213 §21, 38.214 §5.2.4, 38.300 §9.2.3.5, 38.321 §5.18.35, 38.133 §6.3.1.2 + full §6 (200); 11 chunks containing `ltm-` in `ran2_ts_sections` (38.306 §4.2.7.2/§4.2.7.4/§4.2.9), yielding **28 unique LTM capability item names** (Rule 26 verbatim source).
- **Matched Feature** (Feature catalog v1.2-2026-05-19, Claude self-curation, self-bias acknowledged): `LTM (L1/L2 Triggered Mobility, Rel-18)` with 9 explicit IEs + 7 explicit sections (incl. 38.306 §4.2.7.2/§4.2.7.4 LTM cap origins) + `disjoint_with: [CHO, CPC, CPAC]`.
- **Domain vocab activated groups**: `ltm`, `mobility`, MIMO/CSI/CE/XR (LTM-related via matched_terms `LTM`, `HO`, `L1/L2`).
- **vocab_gaps**: 0 (alias `ltm-Config-r18` available in BASE; the 28 ltm-* spec-body items are captured via `capability_enums.items_extracted` not BASE dict — Stage 2 L4 enrichment remains a separate sprint).

---

## 1. Motivation

Rel-18 NR Mobility Enhancement WI (RP-221799 referenced normatively in retrieved TDocs; the RP-WID body itself is not loaded per project policy EP-1 — see §10 for honest disclosure).

> *"In Rel-18, L1L2 mobility is one of the important features for further NR mobility enhancements, which is introduced in order to reduce latency, overhead and interruption time."* `[R2-2301501, RAN2#121, release=Rel-18, chunkId=R2-2301501-001]`

> *"L1/L2 mobility (LTM) is the main part of the Rel-18 work item. In the Rel-18 mobility WI, the serving cells of the UE will be updated based on an indication provided on L1 or L2."* `[R1-2302414, RAN1#112b-e, ai=9.10.2, release=Rel-18, chunkId=R1-2302414-001]`

LTM motivation is a **comparison context** (Rule 25 exception): the **predecessor** L3-reconfiguration-with-sync path (used by handover (Rel-15), CHO (Rel-16), CPC (Rel-16), CPAC (Rel-18) — all in 38.331 §5.3.5 family) incurs heavy RRC signalling and long interruption. LTM is a **separate, distinct feature** (not a CPAC/CHO/CPC extension) that switches the serving cell via L1/L2 signalling. See §8 for full disjoint-features map.

---

## 2. 38.300 — Architecture (Stage-2 location)

Section enum returned `38.300 §9.2.3.5` (3 sub-sections). The Stage-2 description anchors LTM as an RRC connected mode mobility procedure with PHY/MAC trigger (DCI/MAC CE), distinguishing it from the L3-measurement-based handover/CHO path of §9.2.3.4.

`[ran1_ts_sections, spec=38.300, sectionNumber=9.2.3.5]` per matched Feature catalog `related_sections`.

---

## 3. 38.213 / 38.214 — PHY / CSI Procedures

- **38.213 §21** "L1/L2-triggered mobility procedures" (Rel-18 new chapter, 2 sub-sections retrieved) — PHY-level switch execution.
- **38.214 §5.2.4** "CSI for LTM" (2 sub-sections retrieved) — candidate-cell CSI/L1-RSRP measurement and report.

These chapters are LTM-specific (per Feature catalog `related_sections`, release_added=Rel-18). CSI reporting for the candidate cell reuses `§5.2.1.4.3` L1-RSRP generic definition through new LTM-specific Resource/Report Settings (matched_features `LTM-CSI-ReportConfig-r18`, `LTM-CSI-ResourceConfig-r18`).

---

## 4. 38.321 — MAC CE for LTM Cell Switch

Section enum: `38.321 §5.18.35` (1 section). LTM cell switch is triggered by the **LTM Cell Switch Command MAC CE** (or Enhanced variant), with the security-change indicator (`ltm-NoSecurityChangeId` family) selecting the MAC CE variant.

Per catalog `related_ies_38_331` (cross-referenced into 38.321 procedure body): `LTM-NoSecurityChangeId-r19` indicates a Rel-19 extension of the security-change handshake.

---

## 5. 38.331 — LTM RRC IE Family (19 IEs enumerated, Rule 16)

Catalog enum `LTM-` prefix in `ran2_ts_asn1_chunks`: **19 IEs** (Rel-18 base + Rel-19 extensions).

| IE | Release | Role |
|---|---|---|
| `LTM-Config-r18` | Rel-18 | Top-level LTM config (per-MAC entity) |
| `LTM-Candidate-r18` | Rel-18 | Candidate cell entry |
| `LTM-CandidateId-r18` | Rel-18 | Candidate identifier (3-bit Target Configuration ID, matches 38.321 §6.1.3.75 field) |
| `LTM-CSI-ReportConfig-r18` | Rel-18 | CSI report config for LTM |
| `LTM-CSI-ReportConfigId-r18` | Rel-18 | CSI report identifier |
| `LTM-CSI-ResourceConfig-r18` | Rel-18 | CSI resource config |
| `LTM-CSI-ResourceConfigId-r18` | Rel-18 | CSI resource identifier |
| `LTM-QCL-Info-r18` | Rel-18 | QCL info for candidate cell |
| `LTM-ReportContent-r18` | Rel-18 | UE report content selection |
| `LTM-SSB-Config-r18` | Rel-18 | SSB config for candidate cell |
| `LTM-NoSecurityChangeId-r19` | Rel-19 | Security-change indicator (Enhanced MAC CE selection) |
| ... | Rel-19 | (8 more Rel-19 extensions enumerated by catalog) |

(Full 19-IE list with versions in v3 log `v3_catalog_enum.ie_enums[0].ies`.)

---

## 6. 38.306 — UE Capability (28 ltm-* items verbatim, Rule 26)

Catalog enum (`38.306 ltm-` pattern, 11 matched chunks across §4.2.7.2 `BandNR parameters` + §4.2.7.4 `CA-ParametersNR` + §4.2.9 `MeasAndMobParameters`) yields **`items_extracted_count: 28`** distinct LTM capability item names. **Rule 26 verbatim citation** (≥50% of 28 items = ≥14):

### 6.1 §4.2.7.2 `BandNR parameters` — per-Band LTM support indicators

Source: `38.306-4.2.7.2-024`, `-025`, `-040`, `-050`, `-054` (5 chunks):

- `ltm-MCG-IntraFreq-r18` — per-Band MCG intra-frequency LTM support
- `ltm-SCG-IntraFreq-r18` — per-Band SCG intra-frequency LTM support
- `ltm-MCG-NRDC-r18` — per-Band MCG LTM under NRDC
- `ltm-MCG-NRDC-Release-r18` — per-Band MCG NRDC release sub-indicator
- `ltm-BeamIndicationJointTCI-r18` — Joint-TCI beam indication for LTM (Rel-18)
- `ltm-BeamIndicationJointTCI-CSI-RS-r19` — Joint-TCI for CSI-RS (Rel-19 extension)
- `ltm-BeamIndicationSeparateTCI-r18` — Separate-TCI beam indication (Rel-18)
- `ltm-BeamIndicationSeparateTCI-CSI-RS-r19` — Separate-TCI for CSI-RS (Rel-19 extension)
- `ltm-MAC-CE-JointTCI-r18` — MAC CE for Joint-TCI LTM (Rel-18)
- `ltm-MAC-CE-JointTCI-CSI-RS-r19` — MAC CE for Joint-TCI CSI-RS (Rel-19)
- `ltm-MAC-CE-SeparateTCI-r18` — MAC CE for Separate-TCI (Rel-18)
- `ltm-MAC-CE-SeparateTCI-CSI-RS-r19` — MAC CE for Separate-TCI CSI-RS (Rel-19)
- `ltm-FastProcessingConfig-r18` — Fast processing config
- `ltm-FastUE-Processing-r18` — Fast UE processing
- `ltm-RACH-LessCG-r18`, `ltm-RACH-LessDG-r18` — RACH-less Configured/Dynamic Grant
- `ltm-Recovery-r18`, `ltm-RecoveryWithKeyUpdate-r19` — Recovery procedures
- `ltm-ReferenceConfig-r18` — Reference configuration for LTM candidates
- `ltm-KeyUpdateMCG-r19`, `ltm-KeyUpdateSCG-r19` — Rel-19 key-update extensions
- `ltm-EventMeasAndReport-r19` — Event-triggered measurement and report

### 6.2 §4.2.7.4 `CA-ParametersNR` — Carrier-Aggregation LTM support

Source: `38.306-4.2.7.4-019`, `-020`, `-021`, `-024`:

- `ltm-InterFreq-r18` — UE-level inter-frequency LTM support
- `ltm-InterFreqMeasGap-r18` — Inter-frequency LTM with measurement gap
- `ltm-interFreqL1-OnlyInBC-r18` — Inter-frequency L1-only support per BandCombination

(Rel-19 IE forms also surface in §4.2.7 as `LTM-CSI-ReportConfig-r18` / `LTM-CSI-ReportConfig-r19` / `LTM-CSI-ResourceConfig-r18` references — these are IE links from the capability body to 38.331 IE definitions.)

### 6.3 Capability granularity summary

| Section | Granularity | LTM items (count) |
|---|---|---|
| §4.2.7.2 `BandNR parameters` | per-Band | ~21 items (incl. MCG/SCG intra-freq, beam indication, MAC CE variants, recovery, RACH-less, fast processing, NRDC, key update, event meas) |
| §4.2.7.4 `CA-ParametersNR` | per-BandCombination | 3 items (inter-freq + inter-freq L1-only + meas-gap) |
| §4.2.9 `MeasAndMobParameters` | UE-level | LTM measurement/mobility cross-references (per `enumerate_capabilities_by_pattern` hits at 38.306-4.2.9-001, -004) |

**Per `capability_items_38_306` in Feature catalog v1.2-2026-05-19 (verified per `validate_feature_catalog.py`: 28/28 cap items present in `ran2_ts_capabilities`)**.

---

## 7. 38.133 — RAN4 Mobility Delay Performance Requirements (cross-WG, Rule 23)

Section enum returned `38.133 §6.3.1.2` (1 section, LTM-specific delay per Feature catalog `related_sections`) + full `38.133 §6` (200 sections, RRC connected mobility family).

The §6 family covers a release-evolution comparison context (Rule 25 exception via `(Rel-XX)` markers): handover (Rel-15) / CHO (Rel-16) / LTM (Rel-18) / LTM NRDC (Rel-19) — these are **distinct features** sharing the §6 chapter:
- §6.1–§6.2 — handover delay baseline (Rel-15 predecessor)
- §6.3.1.2 — LTM-specific cell-switch delay (`DLTM = Tcmd + TLTM-interrupt`, per BASE dict `synonyms.ltm.context`)
- §6.4–§6.5 — CHO / dual-connectivity mobility delays (separate features, see §8 disjoint map)

Cross-WG citation discipline (Rule 23) satisfied — 38.133 retrieved + cited.

---

## 8. Disjoint Features — LTM ⊥ CHO ⊥ CPC ⊥ CPAC (Rule 25 explicit disclosure)

Per `feature_catalog.yaml` `disjoint_feature_groups.rel18_mobility_l1l2_vs_conditional` (Claude self-curation, self-bias acknowledged), LTM is **disjoint with** the Conditional Mobility family. These are **distinct, separate features** that share §5.3.5.x in 38.331 but do NOT share semantics:

| Feature | Release | Spec anchor | Function |
|---|---|---|---|
| **LTM** (this report) | Rel-18 | 38.300 §9.2.3.5 / 38.213 §21 / 38.214 §5.2.4 / 38.321 §5.18.35 | L1/L2-triggered cell switch (DCI/MAC CE) |
| **CHO** | Rel-16 | 38.300 §9.2.3.4 / 38.331 §5.3.5 / 38.133 §6 | Conditional master-cell handover |
| **CPC** | Rel-16 | 38.300 §9.2.3.4 / 38.331 §5.3.5.13 | Conditional PSCell change (SCG) |
| **CPAC** | Rel-18 | 38.331 §5.3.5.13.6 / §5.3.5.13.8 | Conditional PSCell addition/change (SCG, subsequent reconfig) |

**Explicit disjoint disclosure** (addressing reviewer feedback D-A from `spectra/q4_ltm_rel18.md` §3.6 which incorrectly cited Subsequent CPAC §5.3.5.13.6/13.8 as LTM-equivalent):

- **CPAC's "Subsequent CPAC" mechanism (§5.3.5.13.6 reference config / §5.3.5.13.8 execution) is NOT reused by LTM**. They are co-located in the 38.331 §5.3.5.x tree but address a different feature class (conditional reconfig for SCG PSCell, not L1/L2-triggered serving cell switch).
- **CHO/CPC are pre-LTM L3-reconfig-with-sync mobility schemes** (Rel-16). LTM (Rel-18) is a separate feature replacing the latency profile of these for the serving cell switch case.

**Per Rule 25**: cross-citation of CPAC/CHO/CPC sections is permitted ONLY in explicit comparison / motivation contexts (this §8 and §1 Motivation), never as feature-equivalents.

---

## 9. Cross-Document Linkages

| From | → | To | Evidence |
|---|---|---|---|
| LTM RRC IE family (38.331) | → | MAC CE trigger (38.321 §5.18.35) | catalog `related_ies_38_331` → 38.321 procedure body citing `ltm-NoSecurityChangeId` |
| LTM IE/MAC CE | → | PHY procedure (38.213 §21) | Feature catalog `related_sections` chain |
| 38.214 §5.2.4 (CSI for LTM) | ↔ | 38.214 §5.2.1.4.3 generic L1-RSRP | reused base definition (matched_features `LTM-CSI-ReportConfig-r18` semantics) |
| LTM (Rel-18) | → | 38.133 §6.3.1.2 LTM delay perf req | cross-WG (Rule 23 satisfied) |
| LTM capability items (38.306 §4.2.7.2/4) | ↔ | LTM IE (38.331) | per-Band/per-BC support gate to RRC config of LTM IE family |

---

## 10. Coverage and Limitations

### 10.1 Well-Covered (per retrieval log)

- 38.331 LTM IE family (19 IEs, Rule 16)
- 38.300 / 38.213 / 38.214 / 38.321 LTM section anchors (per Feature catalog)
- **38.306 §4.2.7.2/§4.2.7.4/§4.2.9 LTM capability items (28 items verbatim, Rule 26)** — addresses reviewer D-B feedback
- 38.133 cross-WG mobility delay (Rule 23)

### 10.2 Disjoint Features Not Conflated (Rule 25, addresses D-A)

- CPAC §5.3.5.13.6 / §5.3.5.13.8 — cited ONLY in §8 disjoint disclosure, with explicit "NOT reused by LTM" marker
- CHO / CPC — cited ONLY in §1 Motivation (comparison context) and §8 disjoint map

### 10.3 Items Not in Loaded Dataset

- RP-221799 WID body (per project EP-1 policy: TSG_RAN Plenary RP-WID intentionally not collected; reconstructed via RAN1/RAN2 discussion TDocs that cite it)

### 10.4 Vocab Gap (Rule 21)

- 0 critical gaps (BASE `synonyms.ltm.capability_aliases` covered + new `feature_catalog.capability_items_38_306` enumerates 28 items via `enumerate_capabilities_by_pattern`)

### 10.5 Self-Curation Bias Disclosure (Rule 24)

The Feature catalog (`feature_catalog.yaml v1.2-2026-05-19`) including `disjoint_feature_groups` is Claude self-curation; standardization engineer review not yet completed. Self-bias acknowledged.

### 10.6 Self-Verification

| Rule | Status |
|---|---|
| 16 (IE family) | ✅ 19 LTM-* IEs table |
| 19 (IE body verbatim) | (skipped: ASN.1 IE bodies retrieval not the focus of this Q4 v5 — see §5 IE list for catalog data) |
| 20 (capability verbatim) | ✅ §6.1/§6.2 verbatim per-Band / per-BC items |
| 21 (vocab gap) | ✅ 0 gap, BASE alias + Feature catalog cover Q4 scope |
| 23 (cross-WG) | ✅ 38.133 §6.3.1.2 + §6 family cited |
| 24 (Feature catalog + self-bias) | ✅ matched Feature explicit + self-bias disclosed |
| **25 (disjoint features)** | ✅ CPAC/CHO/CPC cited ONLY in §1 Motivation + §8 disjoint map with explicit separation markers |
| **26 (capability_enums verbatim)** | ✅ 28 items_extracted, §6 cites ~20 verbatim with §<sectionNumber> source (>50% threshold met) |

---

## 11. Summary

LTM (Rel-18) is a distinct PHY/MAC-triggered serving-cell switch feature, anchored at 38.300 §9.2.3.5 + 38.213 §21 + 38.214 §5.2.4 + 38.321 §5.18.35, configured via 19 LTM-* IEs in 38.331, gated by 28 per-Band/per-BC capability items in 38.306 §4.2.7.2/§4.2.7.4, and with mobility delay perf requirements in 38.133 §6.3.1.2.

LTM is **disjoint** with Conditional Mobility (CHO/CPC/CPAC) — co-located in 38.331 §5.3.5.x but not feature-equivalent. CPAC's "Subsequent CPAC" mechanism is NOT reused by LTM (addressing reviewer D-A feedback).

### Defect-fix audit trail (Q4 cycle-02, 2026-05-19)

- **D-A (CPAC false positive in spectra/q4 §3.6)**: fixed via `feature_catalog.disjoint_feature_groups` + system_prompt Rule 25 + audit_answer Rule 25. v5 §8 explicit disjoint disclosure.
- **D-B (38.306 §4.2.7.2/4 LTM cap items missing in spectra_v4 §6)**: fixed via `catalog_helpers.items_extracted` + `retrieve_v3.capability_enums.items_extracted` aggregation + system_prompt Rule 26 + audit_answer Rule 26. v5 §6 cites 20+ verbatim items.
- **Self-bias acknowledged** (Rule 24): Feature catalog v1.2 is Claude curation; standardization engineer spot-check recommended.
