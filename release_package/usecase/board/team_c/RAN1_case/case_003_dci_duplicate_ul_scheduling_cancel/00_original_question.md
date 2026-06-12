# [RAN1] Whether an existing uplink scheduling is cancelled upon receiving a duplicate DCI

- date: 2025-09-15 10:45:30
- author: anonymous
- category: RAN1(Physical)
- Source: internal engineering board (anonymized).

## Body

Hello.

**[Situation]**

- The UE has received a first DCI, which allocates uplink resources on a first BWP.
- However, before starting the uplink transmission, the UE receives a second DCI, which newly allocates uplink resources on a second BWP.
- The specification states that "the UE is not required to transmit or receive from the end of the third symbol of the slot in which it received the DCI indicating an uplink BWP change, until the beginning of the slot indicated by the DCI."

  Section 12 of 3GPP TS 38.213 V15.3.0 (Release 15)

  12 Bandwidth part operation

  > If a UE detects a DCI format 0_1 indicating an active UL BWP change for a cell, the UE is not required to receive or transmit in the cell during a time duration from the end of the third symbol of a slot where the UE receives the PDCCH that includes the DCI format 0_1 in the scheduling cell until the beginning of a slot indicated by the slot offset value of the time domain resource assignment field in the DCI format 0_1.
  >
  > A UE expects to detect a DCI format 0_1 indicating active UL BWP change, or a DCI format 1_1 indicating active DL BWP change, only if a corresponding PDCCH is received within the first 3 symbols of a slot.

**[Point to be confirmed]**

Therefore, if along the time axis (i.e., from the third symbol of the slot in which the DCI was received until the time-axis offset) the first uplink resource allocation and the second uplink resource allocation overlap, I understood that even though the first DCI had already allocated uplink resources, receiving the second DCI anew before transmission begins invalidates (overrides) the scheduling according to the first DCI. In a case such as the above, is my understanding correct that the scheduling according to the first DCI is invalidated (cancelled)?

Thank you.

## Comments (2)

### [1] anonymous (asking engineer follow-up) — 2026-04-04 20:17

Thank you for the answer. I have an additional question.

If the first DCI operates on the default/currently active BWP and does not indicate a BWP change but simply conveys a "resource allocation," can the scheduling by the first DCI still be invalidated?

### [2] anonymous (standards team) — 2025-09-16 13:14

Hello. This is the standards team.

In the specification, the UE performs neither transmission nor reception during the interval you described, after it has received the first DCI. Therefore, if the second DCI comes after the first DCI, the UE does not receive the second DCI, and so it follows the operation indicated by the first DCI.
