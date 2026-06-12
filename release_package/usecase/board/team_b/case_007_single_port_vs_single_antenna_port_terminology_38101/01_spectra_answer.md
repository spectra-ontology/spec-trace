# SPECTRA Answer — Semantic equivalence of "single-port transmission" vs "single antenna-port"

> Regenerated: via the SPECTRA retrieval pipeline
> Question source: `00_original_question.md`

---

## Conclusion (summary)

**The answer to both questions is "yes."**

1. **"single-port transmission" (the Rel-16 §6.2.1 wording) and "single antenna-port PUSCH transmission by DCI format 0_0 or DCI format 0_1..." (Rel-17 §6.2D.1) refer to the same scheduling condition — a PUSCH transmission scheduled on one antenna port.** The Rel-17 expression states the same condition more precisely (making the scheduling trigger and codebook condition explicit), and the two may be interpreted as semantically identical.
2. **The "single antenna port" here is a logical antenna port, not a physical single antenna/connector.** This is not an inference but a conclusion forced by the Rel-16 sentence itself — that sentence stipulates that "the maximum output power for single-port transmission = the sum of the output of **both** antenna connectors," and if 'port' meant a physical connector, a rule that sums two connectors for a single-port transmission could not even be stated coherently. A PC1.5 UE is built to **transmit one logical port over two physical connectors (two PAs)**, and both phrasings address that situation.

## 1. "antenna port" is by definition a logical concept (TS 38.211 §4.4.1)

> "An antenna port is defined such that the channel over which a symbol on the antenna port is conveyed can be inferred from the channel over which another symbol on the same antenna port is conveyed."

An antenna port is a logical concept defined as a unit of channel inference, and is not in 1:1 correspondence with physical antennas or connectors. TS 38.101-1 does not redefine "antenna port" on its own; it uses this concept as-is.

## 2. DCI 0_0 scheduling = single antenna port transmission (TS 38.214 §6.1.1)

> "If PUSCH is scheduled by DCI format 0_0, the PUSCH transmission is based on a single antenna port."

The §6.2D.1 wording "single antenna-port PUSCH transmission by DCI format 0_0 or by DCI format 0_1 for single antenna port codebook based transmission" carries over this transmission-scheme condition (one logical port) verbatim. For DCI format 0_1, it refers to the case where a single antenna port is indicated in codebook based transmission.

## 3. RAN4 terminology: the physical measurement point is separately called the "antenna connector" (TS 38.101-1 §6.1)

> "Unless otherwise stated, the transmitter characteristics are specified at the antenna connector of the UE..."

When TS 38.101-1 refers to the physical measurement point, it consistently uses the term **antenna connector**. Within the same document, therefore, "port" and "connector" are distinct terms, and reading "single antenna port" as "single connector" conflicts with this terminology system. The Rel-16 sentence in your question demonstrates exactly that distinction: the maximum output power for single-**port** (logical) transmission is defined as the sum from both UE antenna **connectors** (physical).

## 4. The background document makes the logical port ↔ physical TX chain mapping explicit (TR 38.837 §5.3)

TR 38.837, which records the background of the Rel-17 Tx Diversity discussion (approved change request R4-2210708, CR0004r1), explicitly addresses the relationship between ports and physical chains:

> "One potential implementation that could be considered is to virtualize two antenna port transmission by transmitting one port as the sum of the TX chains, and the other as the difference of the two chains."

In other words, an implementation that virtualizes one logical port as the sum/difference of two physical TX chains is the premise of the standards discussion, and Table 5.3.1-1, which summarizes how the "single antenna-port requirement" applies, likewise keeps the two separated: the applicability condition is stated in terms of logical-port scheduling ("scheduled for single antenna-port transmission by DCI format 0_0 or by DCI format 0_1 for codebook-based transmission on a single antenna port"), while the resulting applicability is stated in terms of physical configuration ('Single TX'/'Dual TX' — §6.2 vs §6.2G requirements).

## 5. Relationship between the two expressions

| Item | Rel-16 §6.2.1 wording | Rel-17 §6.2D.1 wording |
|---|---|---|
| Expression | "maximum output power for single-port transmission" + "scheduled by DCI format 0_0 or by DCI format 0_1 configured for single antenna port" | "scheduled for single antenna-port PUSCH transmission by DCI format 0_0 or by DCI format 0_1 for single antenna port codebook based transmission" |
| Condition referred to | PUSCH transmission scheduled on one (logical) antenna port | Identical |
| Scope of application | PC1.5 only (MOP met by summing the two connectors) | General across all power classes (§6.2.2 applies per ue-PowerClass; §6.2G exception when TxD is supported) |
| Notes | The first half of the Rel-16 sentence also doubles as the summation rule | The summation rule is moved out to §6.2G.1 ("the maximum output power ... is defined as the sum of the maximum output power from all UE transmit antenna connectors"); it is explicitly stated that this applies to PC1.5 even without the TxD capability being reported |

In short, Rel-16's "single-port transmission" is the same concept, made more precise in Rel-17 as "single antenna-port PUSCH transmission (by DCI 0_0 / DCI 0_1 single antenna port codebook)"; what changed is not the meaning of the term but the **structural placement of the requirement** (a PC1.5-specific sentence → the §6.2D fallback provision + the §6.2G Tx Diversity general provision). The history of this structural change is traced change-request by change-request in a separate inquiry (Case-004).

## Verification scope and limitations

- The term definition was quoted directly from TS 38.211 §4.4.1, the transmission-scheme condition from TS 38.214 §6.1.1, and the RAN4-side usage from the body text of TS 38.101-1 §6.1/§6.2D.1/§6.2G.1.
- The absence of an "antenna port" definition in TS 38.101-1 §3 (the definitions clause) was confirmed by a term-index search; accordingly, the point that the 38.211 definition applies is the standard interpretation under the 3GPP document hierarchy.
- The virtualization implementation description (TR 38.837) is an example at the "potential implementation" level and does not prescribe any specific UE implementation.
