# SPECTRA Answer — Periodic HPLMN/higher priority PLMN search (BPLMN search): full frequency scan vs stored frequency scan

> Retrieval method: 3GPP TS spec body text was searched with semantic embeddings (vector similarity), and the clause-structure tree of the standards documents was exhaustively enumerated via the knowledge graph to identify the governing clauses in a vocabulary-independent way. Because this question spans NAS procedures (TS 23.122) and AS procedures (TS 38.304) and has a conformance-testing angle, **the conformance test spec (TS 38.523-1) partition and the change request (CR) partition were also searched**. The NAS spec body was cross-checked against the public 3GPP archive original.

## Conclusion

**Starting with stored frequencies is, in itself, an optimisation that the spec explicitly permits. However, an implementation with no path at all to expand to a full frequency scan when the target PLMN is not found on the stored frequencies (permanent stored-only) carries violation risk.** The spec-safe design is "stored-first → expand to a full band scan if not found."

The supporting structure splits into two layers:

- **NAS layer (TS 23.122 §4.4.3.3.1)** — defines the *obligation and target* of the periodic search: while in a VPLMN, the MS shall periodically (timer T) attempt to obtain service on the HPLMN/EHPLMN/higher priority PLMN, and that attempt is performed *"by scanning in accordance with the requirements that are applicable to i), ii) and iii) as defined in the Automatic Network Selection Mode"*. In other words, NAS does not specify which frequencies to sweep or how — it delegates that to the search procedure requirements.
- **AS layer (TS 38.304 §5.1.1)** — defines the *method* of the search: *"On request of the NAS, the AS shall perform a search for available PLMNs and report them to NAS."* [38.304 §5.1.1.1] The baseline obligation in §5.1.1.2 is *"The UE shall scan all RF channels in the NR bands according to its capabilities to find available PLMNs"*, but **the same clause explicitly permits an optimisation**: *"The UE may optimise PLMN search by using stored information e.g. frequencies and optionally also information on cell parameters from previously received measurement control information elements."* [38.304 §5.1.1.2]

So a standards basis for "using stored frequencies" does exist (may optimise), but it is **a means of making the search faster**, not **an exemption that allows the search scope to be confined to the stored list**. The baseline obligation ("shall scan all RF channels … to find available PLMNs") remains in force.

## Verdict by scenario

| Implementation | Verdict | Basis |
|---|---|---|
| **A. Stored-first, and the target PLMN is found on a stored frequency** | Not a violation | The optimisation sentence in §5.1.1.2 permits exactly this design. The purpose of the search (finding and reporting the target PLMN) is achieved |
| **B. Permanent stored-only (no full scan even when not found)** | **Violation risk** | The "shall scan all RF channels" obligation of §5.1.1.2 is never fulfilled at any point. An HPLMN that exists only on frequencies/RATs outside the stored list is structurally never found → the available PLMNs reported to NAS are based on an incomplete search. In 23.122 §4.4.3.3.1 e) *"If the HPLMN … is not found, the MS shall remain on the VPLMN"*, "not found" must be the outcome of scanning in accordance with the i)–iii) requirements. Conformance testing also verifies this case directly (see the conformance section below) |
| **C. Differentiated per cycle (e.g., stored every cycle, full scan every N cycles)** | Potentially permissible (with a caveat) | No single clause mandating full-scan completeness per cycle was found within the examined scope (enumeration of the entire 38.304 clause-title tree + full reading of candidate clauses) — an implementation-discretion area. However, "a path that finds an available HPLMN within finite time" must be guaranteed; without such a path, this converges to B |

## A frequently confused clause — the "stored parameter values" in §5.2.3.2 are not a basis for a stored frequency scan

TS 38.304 §5.2.3.2 (Cell Selection Criterion) contains wording related to the periodic search and is easily mistaken as a basis for a stored frequency scan:

> *"The signalled values Qrxlevminoffset and Qqualminoffset are only applied when a cell is evaluated for cell selection as a result of a periodic search for a higher priority PLMN while camped normally in a VPLMN (TS 23.122 [9]). During this periodic search for higher priority PLMN, the UE may check the S criteria of a cell using parameter values stored from a different cell of this higher priority PLMN."* [38.304 §5.2.3.2]

What is permitted to be stored and reused here are **the S-criterion evaluation parameter values** (the UE may pre-evaluate the S criterion using Qrxlevmin-type values stored from a different cell of the same higher priority PLMN); it does **not mean the set of frequencies to scan may be confined to the stored list.** The role of this clause is (1) to apply the Qrxlevminoffset/Qqualminoffset offsets only during the periodic search, giving a margin against ping-pong movement to the higher priority PLMN, and (2) to allow candidate-cell evaluation to begin before re-receiving that cell's system information. The clauses that actually support using stored *frequencies* are, separately, §5.1.1.2 (PLMN search optimisation) and §5.2.3.1 b) (cell selection by stored information).

One more confusion to watch for: the RAN4 RRM requirement [38.133 §4.2.2.7], *"the UE shall search every layer of higher priority at least every Thigher_priority_search = (60 * Nlayers) seconds, where Nlayers is the total number of higher priority NR and E-UTRA carrier frequencies **broadcasted in system information**"*, is a search-periodicity requirement for **cell reselection priority layers** (reselection priorities broadcast in SIBs), which is a mechanism separate from the **periodic higher priority *PLMN* search** in this question (USIM-stored timer T, 23.122) — the shared phrase "higher priority" causes frequent mix-ups, but the former is reselection within the same PLMN, the latter is selection between PLMNs.

## The spec's own design pattern — stored-first + expansion fallback

The cell selection procedure codifies this pattern within the same spec [38.304 §5.2.3.1]:

> *"a) Initial cell selection (no prior knowledge of which RF channels are NR frequencies): 1. The UE shall scan all RF channels in the NR bands according to its capabilities to find a suitable cell. …*
> *b) Cell selection by leveraging stored information: 1. This procedure requires stored information of frequencies and optionally also information on cell parameters from previously received measurement control information elements or from previously detected cells. 2. Once the UE has found a suitable cell, the UE shall select it. **3. If no suitable cell is found, the initial cell selection procedure in a) shall be started.**"*

The stored-information-based procedure (b) is permitted, but on failure the all-channel scan (a) **"shall be started"** — the expansion is mandatory. PLMN search (§5.1.1.2) has no separate stepwise fallback sentence like this, but the combination of the baseline obligation ("shall scan all RF channels") + the "may optimise" structure yields the same conclusion: start with the optimisation, and if the goal (finding the target PLMN) is not met, widen to the scope of the baseline obligation.

For reference, the AS/NAS functional split table [38.304 §4.2 Table 4.2-1] also defines the AS role in PLMN Selection as *"search for available PLMNs"* + *"Report available PLMNs … to NAS on request from NAS or autonomously"*, and the NAS role as maintaining the priority list, selection, and evaluation — the separation whereby the authority on the scan method lies with 38.304 (AS part) and the authority on the periodicity and targets lies with 23.122 (NAS part) is built into the spec structure itself.

## NAS layer detail (TS 23.122 §4.4.3.3.1 — cross-checked against the public archive original)

> *"If the MS is in a VPLMN, the MS shall periodically attempt to obtain service on its HPLMN (if the EHPLMN list is not present or is empty) or one of its EHPLMNs (if the EHPLMN list is present) or a higher priority PLMN/access technology combinations listed in 'user controlled PLMN selector' or 'operator controlled PLMN selector' **by scanning in accordance with the requirements that are applicable to i), ii) and iii)** as defined in the Automatic Network Selection Mode in subclause 4.4.3.1.1."*

- **Timer T**: *"a value T minutes may be stored in the SIM, T is either in the range 6 minutes to 8 hours in 6 minute steps or it indicates that no periodic attempts shall be made. If no value is stored in the SIM, a default value of 60 minutes is used."* (The USIM storage field for T is EF_HPPLMN, Higher Priority PLMN search period — TS 31.102)
- Accompanying requirements: a) periodic attempts apply only in automatic mode and while roaming, b) the first attempt after power-on is between a minimum of 2 minutes and a maximum of T minutes, d) performed in idle mode only, e) remain on the VPLMN if not found, f) limited to PLMN/access technology combinations of the same country.
- §4.4.3.1.1 i)–iii) define the **PLMN list** in the priority order HPLMN(/EHPLMN) → User Controlled PLMN Selector → Operator Controlled PLMN Selector. Accompanying requirement c) states that when an access technology is specified in the selector list, *"the MS should limit its search for the PLMN to the access technology or access technologies associated with the PLMN"* — i.e., the search narrowing that NAS permits is along the **access technology axis**, not along a stored-frequency-list axis.

The wording of this NAS clause is also quoted verbatim in the RAN conformance test spec body (the reference clause of TS 38.523-1 §6.2.1.5 — the sentence above is reproduced there together with the note "Unless otherwise stated these are Rel-15 requirements").

## Conformance perspective — the tests that catch stored-only

Conformance testing directly verifies "discovery of a higher priority PLMN that lies outside the stored list":

- **38.523-1 §6.2.1.5 — Inter-RAT Background HPLMN Search / Search for correct RAT for HPLMN / Automatic Mode**:
  > *"with { UE in Automatic network selection mode is camped on a E-UTRAN VPLMN cell and HPLMN cell available on NR } ensure that { when { higher priority PLMN search timer T expires } then { UE detects NR cell and camps on the NR cell } }"*

  While camped on an E-UTRA VPLMN, the HPLMN exists **only on NR** — a setup in which the NR frequency may well be absent from a stored frequency list built from recent camping history; to PASS, the UE must detect and camp on the NR cell when T expires. A stored-only implementation can permanently fail to find the HPLMN in this setup.
- **38.523-1 §6.1.1.6 — PLMN selection / Periodic reselection / MinimumPeriodicSearchTimer**: with a higher priority PLMN cell available while camped on a VPLMN, verifies the first-attempt timing (*"the MS shall make the first attempt to access the HPLMN or an EHPLMN or higher priority PLMN after a period of at least 2 minutes"*) and the lower bound of T (MinimumPeriodicSearchTimer) — the *performance itself* of the periodic search is under test.
- For reference: 38.523-1 §6.1.1.5/§6.1.1.7 (PLMN selection of RPLMN, HPLMN/EHPLMN … / Automatic mode) — verify priority-ordered (E)HPLMN selection in automatic mode.

## Implementation guidance (summary from the current-consumption perspective)

1. **Keep stored-first as-is** — §5.1.1.2's *"may optimise PLMN search by using stored information e.g. frequencies"* is the explicit basis. Most of the current savings come from here (search ordering) and from the T periodicity.
2. **Always provide an expansion path** — when the target PLMN is not found on the stored frequencies, expand to a band scan within the UE's capability range, either within the same cycle or within a finite number of cycles. A design that guarantees "an available HPLMN can be found within finite time" satisfies both the intent of 23.122 §4.4.3.3.1 and the 38.523-1 test setups.
3. **Include the inter-RAT case** — 23.122 i)–iii) operate at the granularity of PLMN/access technology combinations. When an access technology is specified in the selector list, restriction to that RAT is possible ("should limit … to the access technology"), but this is not a basis for restriction to a stored frequency list. The §6.2.1.5 test looks at exactly this inter-RAT discovery.
4. **Use the evaluation-stage optimisation separately** — the UE may pre-evaluate the S-criteria using parameter values stored from a different cell of the same higher priority PLMN (§5.2.3.2), and the Qrxlevminoffset/Qqualminoffset margins apply only during the periodic search — these are power-saving/stabilisation means at the post-discovery evaluation stage, not the scan scope.

## Coverage / limitations

- The primary corpus for this analysis is the RAN specs (TS 38.304, 38.300, 38.523-1, etc.). The NAS spec **TS 23.122 body is outside the corpus coverage**, so it was checked directly against the public 3GPP archive original, and cross-confirmed to match the identical wording quoted in the conformance test spec body (marked as Rel-15 requirements). Re-checking the original is recommended for possible wording changes in the latest release.
- No clause mandating "a full scan must be completed on every periodic attempt" was **found** within the examined scope (enumeration of the entire 38.304 clause-title tree + full reading of candidate clause bodies + the bodies of 23.122 §4.4.3.3.1/§4.4.3.1.1) — scan scheduling within a cycle is judged to be implementation discretion, but case B in the table above (no discovery path) lies outside that discretion.
- The equivalent E-UTRA-side procedure (TS 36.304) is delegated by 38.304 §5.1.1.3, *"Support for PLMN selection in E-UTRA is described in TS 36.304 [7]"* — the 36.304 body was not quoted directly (referenced but body not fetched).
- The PLMN-reading details cited by §5.1.1.2 (TS 38.331 [3]) are noted as a reference only — referenced from §5.1.1.2 body, section body not directly retrieved.
