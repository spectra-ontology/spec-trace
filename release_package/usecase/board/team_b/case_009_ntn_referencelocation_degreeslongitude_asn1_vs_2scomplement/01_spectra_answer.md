# Case-009 — SPECTRA Answer

> Question: [00_original_question.md](./00_original_question.md)

---

## Conclusion summary

**(B) 2's complement governs.** `ReferenceLocation-r17` is declared as an `OCTET STRING` in TS 38.331, so the RRC ASN.1 decoder (PER) carries its content octets only as an opaque byte string; the bit-level meaning of the content is determined by TS 37.355 `Ellipsoid-Point` (a signed integer field) and its parent definition TS 23.032 §6.1 (24-bit 2's complement). When the conformance test vectors in TS 38.523-1 §8.1.4.4.7.3.3 are worked out numerically, they match the stated latitude/longitude only under (B) and contradict it under (A).

---

## Q1. Which rule governs — (B) 2's complement

The verdict rests on two strands: the chain of standards-body quotations and numerical verification of the conformance vectors.

**① Field definition chain (3GPP body quotations)**

- TS 38.331 ASN.1: `ReferenceLocation-r17 ::= OCTET STRING` — at the RRC level this field is an octet container, not an INTEGER. It is used in SIB19 as `referenceLocation-r17 ReferenceLocation-r17 OPTIONAL, -- Need R`, and the field description specifies its usage (triggering location-based measurements): "Reference location of the serving cell provided via NTN (quasi-)Earth fixed cell … as defined in TS 38.304".
- TS 37.355 `Ellipsoid-Point` (CR0332 approved at RAN2#117-e, original text as contained in R2-2203315):
  > "The IE Ellipsoid-Point is used to describe a geographic shape **as defined in TS 23.032** [15]. `Ellipsoid-Point ::= SEQUENCE { latitudeSign ENUMERATED {north, south}, degreesLatitude INTEGER (0..8388607), -- 23 bit field, degreesLongitude INTEGER (-8388608..8388607) -- 24 bit field }`"

  The very fact that the range of `degreesLongitude` is declared as a **signed range (−8388608..8388607)** gives this 24-bit field the semantics of carrying a signed number. The bit coding of the shape is delegated to TS 23.032.
- TS 23.032 §6.1 (publicly available 3GPP edition, ETSI TS 123 032): "longitude, expressed in the range −180°, +180°, coded as a number between **−2^23 and 2^23−1, coded in 2's complement binary on 24 bits**."
- The same coding is also explicitly written into the RAN5 test equipment definitions (TS 36.509 update CR, original text as contained in R5-230120 — the definition lineage pointed to by the Derivation Path of the 38.523-1 test vectors):
  > "DLO23..DLO0 = 'degreesLongitude' value −8388608..8388607 (**two's complement binary** coded in a fixed length of **24 bits**, DLO23 is most significant bit and DLO0 is least significant bit)."

**② Why (A) does not apply** — The ITU-T X.691 "n−lb" offset encoding is a rule that a PER encoder applies **when encoding an ASN.1 INTEGER type**. From the RRC (38.331) perspective this field is an OCTET STRING, not an INTEGER, so there is simply no place for the PER constrained-INTEGER rule to come into play (see Q2 for details). The interpretive authority over the 24-bit value therefore lies with the content definitions (23.032/37.355).

**③ The conformance vectors empirically confirm (B)** — see Q3.

---

## Q2. The role of the `::= OCTET STRING` declaration — blocking the PER path + carrying the 23.032 bytes directly

- **Blocking the PER path**: PER's per-INTEGER offset ("n−lb") encoding occurs when an ASN.1 compiler encounters an INTEGER type. The `ReferenceLocation-r17 ::= OCTET STRING` declaration makes the RRC encoder/decoder treat the content as opaque octets, so the RRC ASN.1 stack applies no integer transformation whatsoever to the latitude/longitude inside this field.
- **The content is a directly packed fixed-width bit layout**: the content octets are not "a PER-encoded LPP message"; they carry the 23.032 coding result as-is (latitudeSign 1 bit + degreesLatitude 23 bits + degreesLongitude 24 bits, MSB-first). This is confirmed by the test vector arithmetic (Q3) — if the content were PER-encoded, the same hex would yield a different longitude, contradicting the latitude/longitude stated in the test specification.
- **Established practice of the same kind within 38.331**: other location fields in 38.331 spell out the same pattern. For example, the `coarseLocationInfo` field description — "Parameter type **Ellipsoid-Point defined in TS 37.355** [49]. **The first/leftmost bit of the first octet contains the most significant bit**." (UEInformationResponse / MeasResult family). In other words, "OCTET STRING container + 37.355 shape packed directly MSB-first" is an established coding practice throughout 38.331, and it matches the identical wording the original question quoted for `ReferenceLocation`.

---

## Q3. Numerical verification of the test vectors — they match only under (B)

Values stated in TS 38.523-1 §8.1.4.4.7.3.3 (NR NTN CHO, CondEventD1):

| Test parameter | Hex | Stated latitude/longitude |
|---|---|---|
| `referenceLocation1-r17` | `'2240 DC56 7176'H` | Lat 24.08439333 / Lon 121.56076999 |
| `referenceLocation2-r17` | `'2519 0956 7176'H` | Lat 26.08439333 / Lon 121.56076999 |
| `ellipsoidPointWithAltitude` | `'2519 0956 7176 0000'H` | (same coordinates as above + altitude 0) |

Bit decomposition (48 bits = sign 1 + lat 23 + lon 24):

- **Latitude** (`referenceLocation1`): leading 1 bit = 0 (north), next 23 bits = 0x2240DC = 2,244,828 → 2,244,828 × 90/2^23 = **24.08439°** ✓ (referenceLocation2: 0x251909 = 2,431,241 → **26.08439°** ✓)
- **Longitude** 24 bits = `0x567176` = 5,665,142 (MSB=0, positive):
  - **(B) 2's complement**: +5,665,142 × 360/2^24 = **+121.56076°** → **matches** the stated value 121.56076999 ✓
  - **(A) offset binary (n−lb, lb=−2^23)**: 5,665,142 − 8,388,608 = −2,723,466 → −2,723,466 × 360/2^24 = **−58.44°** → **contradicts** the stated value ✗

Only (B) holds for both vectors. In other words, the RAN5 conformance tests are written so that a UE passes only when it interprets these octets as 2's complement.

---

## Implementation guide (modem decoder perspective)

1. Take the `ReferenceLocation-r17` octets from the RRC ASN.1 decoder output (byte string) and decompose them with **fixed-bit-offset parsing**: bit0 = latitudeSign, bit1..23 = degreesLatitude (unsigned), bit24..47 = degreesLongitude (**signed 24 bits → sign-extend to 32 bits**).
2. Do not apply an offset correction (−2^23) to degreesLongitude — that transformation belongs only to PER INTEGER encoding and does not apply to this field.
3. Conversion formulas: longitude = N × 360/2^24 (N = the 2's complement interpreted value), latitude = N × 90/2^23 (apply south/north via latitudeSign).
4. The same rule applies to the other Ellipsoid-Point-carrying fields in 38.331 (`coarseLocationInfo`, etc.) and to the reference locations in the NTN neighbour cell information (`NTN-NeighbourCellInfo`).

## Applicability scope (Release)

- `ReferenceLocation-r17` = introduced with Rel-17 NTN (SIB19). From Rel-18 onward its usage expands via `NTN-NeighbourCellInfo-r18` and similar, with the coding rule unchanged.
- The test vectors above are based on the Rel-18 edition of TS 38.523-1.

## Evidence source boundary

- Direct quotations from 3GPP bodies: TS 38.331 (ASN.1 · SIB19 · field description), TS 38.304 §5.2.4.2 (usage procedure), TS 37.355 Ellipsoid-Point (original text of the RAN2-approved CR), TS 36.509 test definitions (original text of the RAN5-approved CR), TS 38.523-1 §8.1.4.4.7.3.3 (test vectors).
- The TS 23.032 §6.1 body text and the ITU-T X.691 body text are outside the scope of the in-house standards document holdings, so they were cross-checked against publicly available editions [web: ETSI TS 123 032 §6.1 — "coded in 2's complement binary on 24 bits"]. Even without this external reference, the verdict (B) stands independently on the in-house holdings alone (the 37.355 signed range + the explicit two's complement wording in 36.509 + the 38.523-1 vector arithmetic).
