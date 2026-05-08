# Summary of Rel.16 enhanced Type-II codebook standardization items

> This document is a first-pass analysis of the Rel.16 enhanced Type-II codebook from the perspective of WID motivation, 38.211, 38.212, 38.214, 38.306, 38.331, and 38.521-4, focused on cross-document linkages.
> Note: The `38.512-4` mentioned in the question is interpreted, in the context of NR UE performance, as `TS 38.521-4: NR UE conformance specification; Radio transmission and reception; Part 4: Performance`.

---

## 1. Motivation: why was Rel.16 enhanced Type-II needed

The Rel.15 Type-II CSI codebook was designed to improve MU-MIMO performance through high-resolution PMI feedback, but its CSI feedback overhead is large; in particular, when many wideband/subband coefficients must be reported, uplink control overhead becomes a problem.

The core direction of the Rel.16 MIMO enhancement is the following.

```text
Rel.15 Type-II
  Enables high-resolution CSI
  But coefficient reporting payload is large
  Has rank-extension and overhead issues

Rel.16 enhanced Type-II
  spatial-domain basis + frequency-domain basis + coefficient sparsity
  Only the necessary coefficients are selected/reported
  MU-MIMO scheduler can build a more refined precoder
  Overhead is controlled relative to Rel.15 Type-II
```

In other words, the Rel.16 enhanced Type-II codebook is not simply a more complex codebook; it is a **structure that lets the MU-MIMO scheduler obtain more refined channel-direction information while still controlling CSI feedback overhead**.

---

## 2. Cross-document flow

```text
38.331
  Configures typeII-r16 or related Type-II in CSI-ReportConfig / CodebookConfig-r16
  Configures CSI measurement resources via NZP-CSI-RS-ResourceSet / CSI-RS-ResourceMapping
      ↓
38.211
  Defines how CSI-RS resources are actually mapped to RE/port/CDM/frequency/time positions
      ↓
38.214
  UE measures CSI-RS and computes PMI/RI/CQI based on the enhanced Type-II codebook
      ↓
38.212
  Computed RI/CQI/PMI/non-zero coefficient information is encoded into UCI Part 1/Part 2 bit fields
      ↓
38.306
  UE reports as capability whether it supports the enhanced Type-II codebook, port-selection, and rank/port combinations
      ↓
38.521-4
  Conformance test verifying that the CSI reporting feature meets the required performance under actual radio conditions
```

The key point is that **38.331 lays out the configuration, 38.211 defines the actual physical resources for CSI-RS, 38.214 defines the codebook math/procedure, 38.212 defines the UCI bit field, and 38.306/38.521-4 take care of capability and performance verification respectively**.

---

## 3. 38.331: RRC parameters

RRC primarily configures two things.

First, **what to measure**. CSI-RS resources are configured via `NZP-CSI-RS-ResourceSet`, `NZP-CSI-RS-Resource`, `CSI-RS-ResourceMapping`, etc. `CSI-RS-ResourceMapping` includes fields such as `frequencyDomainAllocation`, `nrofPorts`, `firstOFDMSymbolInTimeDomain`, `cdm-Type`, `density`, and `freqBand`.

Second, **which codebook to use for CSI reporting**. The Type-II codebook is configured under the `CodebookConfig` family inside `CSI-ReportConfig`; in Rel.16 the `typeII-r16` family of settings goes inside `CodebookConfig-r16`.

| RRC area | Role |
|---|---|
| `CSI-ReportConfig` | CSI reporting mode, periodicity, codebook type, report quantity |
| `CodebookConfig-r16` | Settings related to the Rel.16 enhanced Type-II codebook |
| `CSI-ResourceConfig` | Linkage to the resource set targeted for CSI measurement |
| `NZP-CSI-RS-ResourceSet` | Bundle of one or more NZP CSI-RS resources |
| `NZP-CSI-RS-Resource` | Individual CSI-RS resource |
| `CSI-RS-ResourceMapping` | CSI-RS port count, RE positions, CDM, density, RB range |

From the RRC perspective, the enhanced Type-II codebook does not exist in isolation; it is **a feature in which CSI-RS resource configuration and CSI report configuration are combined**.

---

## 4. 38.211: CSI-RS resource configuration

38.211 defines how CSI-RS is mapped onto physical resources. CSI-RS resource mapping involves the following elements.

| Item | Meaning |
|---|---|
| `nrofPorts` | Number of CSI-RS antenna ports |
| `frequencyDomainAllocation` | RE arrangement in the frequency domain |
| `firstOFDMSymbolInTimeDomain` | Starting OFDM symbol in the time domain |
| `cdm-Type` | CDM scheme |
| `density` | CSI-RS density |
| `freqBand` | RB range over which CSI-RS is placed |

From the enhanced Type-II codebook's perspective, the important point is that **the CSI-RS port count and resource configuration determine the codebook dimensions**.

```text
RRC's nrofPorts / CSI-RS resource set
  ↓
CSI-RS port and RE mapping in 38.211
  ↓
UE measures the corresponding CSI-RS
  ↓
Spatial/frequency basis and coefficient computation in the 38.214 codebook
```

In particular, the benefits of the Type-II codebook grow with high-order MIMO and many antenna ports, so CSI-RS port configuration is a prerequisite for the enhanced Type-II codebook.

---

## 5. 38.214: codebook definition

38.214 defines, given the CSI-RS measurements at the UE, which codebook structure is used to construct the PMI. The core of Rel.16 enhanced Type-II is not simply "picking one beam index"; instead, **multiple basis vectors and coefficients are used to build the precoding matrix**.

The behavior can be written briefly as follows.

```text
1. UE measures CSI-RS
2. Selects spatial-domain basis candidates
3. Selects frequency-domain basis candidates
4. Computes per-layer coefficients
5. Selects only the meaningful non-zero coefficients
6. Composes RI/CQI/PMI/LI/non-zero coefficient information into a CSI report
```

The key concepts here are the following.

| Concept | Meaning |
|---|---|
| spatial-domain basis | Basis in the antenna/beam-direction domain |
| frequency-domain basis | Basis used to express frequency-selective channel variations |
| coefficient | Weights that combine the chosen basis vectors |
| non-zero coefficient | Meaningful coefficients that will actually be reported |
| bitmap | Indicates which basis/coefficients were selected |
| RI/CQI/PMI/LI | CSI information related to rank, channel quality, precoder matrix, and layer indicator |

That is, enhanced Type-II can be understood as **a structure that represents the channel through a sparse combination of basis vectors in order to reduce feedback overhead**.

---

## 6. 38.212: UCI field information

38.212 defines how a CSI report is encoded into the UCI bitstream. Type-II family CSI reports are typically split into **Part 1** and **Part 2**.

| UCI part | Main contents |
|---|---|
| CSI Part 1 | RI, CQI, total number of non-zero coefficients, and other information needed to decode Part 2 |
| CSI Part 2 | Detailed information related to PMI, LI, and coefficients |

If 38.214 defines "what information must be computed", then 38.212 defines "how that information is carried, in how many bits, on UCI".

Document linkage is as follows.

```text
38.214
  UE computes RI/CQI/PMI/LI/coefficient information
      ↓
38.212
  Bit encoding into CSI Part 1 / Part 2 fields
      ↓
CSI report is transmitted over PUCCH or PUSCH
```

In enhanced Type-II, Part 1 is important because the payload size of Part 2 can vary with RI and the number of non-zero coefficients. That is, Part 1 is not just plain CSI; it also functions as **meta-information for interpreting Part 2**.

---

## 7. 38.306: UE capability

38.306 reports, as UE capability, which Type-II/eType-II codebook combinations the UE supports. Capability is the upper bound that the gNB must respect when issuing RRC configuration.

Important capability categories include the following.

| Capability category | Meaning |
|---|---|
| enhanced Type-II rank support | Whether rank 1/2 or higher is supported |
| Number of supported CSI-RS ports | How many CSI-RS ports the codebook can be processed against |
| port-selection Type-II support | Whether port-selection-based Type-II codebook is supported |
| frequency-domain compression support | Whether FD-basis-based compression is supported |
| Coefficient reporting combinations | Supported combinations of non-zero coefficient count and amplitude/phase reporting |

The linkages are as follows.

```text
If UE capability does not support enhanced Type-II
  → gNB must not provide that CodebookConfig

If UE capability supports only certain rank/port combinations
  → RRC's CSI-RS port count, CodebookConfig, and report setting must be configured within that range

If UE capability supports port-selection Type-II
  → gNB may configure port-selection-based CSI reporting
```

Therefore, 38.306 defines the **possible scope** of scheduler/RRC configuration.

---

## 8. 38.521-4: performance requirements

The 38.512-4 in the question is interpreted as 38.521-4. 38.521-4 is the NR UE radio transmission/reception performance conformance document and includes the conducted requirements for CSI reporting.

The CSI reporting requirements in 38.521-4 verify whether the UE can correctly report CSI under specified CSI-RS/channel conditions.

The connection structure is as follows.

```text
38.331/38.211
  CSI-RS and codebook configuration
38.214
  UE computes PMI/CQI/RI
38.212
  UCI encoding
38.521-4
  Verifies whether this CSI reporting meets the required performance under test conditions
```

From the performance requirement perspective, the following items matter.

| Item | Meaning |
|---|---|
| CSI reporting accuracy | Whether the UE properly reports the required PMI/CQI/RI |
| multiple PMI/reporting scenario | Accuracy under multi-PMI or complex CSI report situations |
| Type-II/eType-II optional feature test | Performance verification of the relevant feature for UEs that support the capability |
| FR1/FR2 conditions | Test configuration depending on band and RF conditions |
| 2Rx/4Rx, Tx port combinations | Verification across UE RF chain and CSI-RS port combinations |

---

## 9. Final summary

```text
Rel.16 MIMO WID
  → Improve MU-MIMO performance and reduce CSI overhead
  → 38.331 configures CSI-RS/codebook reporting
  → 38.211 defines CSI-RS resource mapping
  → 38.214 computes the enhanced Type-II codebook
  → 38.212 defines the UCI Part 1/2 bit fields
  → 38.306 limits the UE-supported capability
  → 38.521-4 verifies CSI reporting performance
```

The enhanced Type-II codebook is **a feature in which CSI-RS measurement resources, codebook computation, UCI encoding, UE capability, and conformance requirements are tightly linked**. Therefore, rather than reading any single clause in isolation, one must trace the document flow above to properly understand standard behavior.

---

## References

- 3GPP TS 38-series list: https://www.3gpp.org/dynareport/38-series.htm
- 3GPP TS 38.211, 38.212, 38.214, 38.306, 38.331
- 3GPP TS 38.521-4
- 5G Americas, 5G Evolution: 3GPP Releases 16 and 17 overview
