# Case-001 — Whether a Registration request is sent after PDU release reject (cause #43, Invalid PDU session identity)

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> Case number: case-001

---

## Question body (meaning preserved verbatim from the original)

The UE sends a PDU release request. The network responds with a PDU release reject, cause #43 (Invalid PDU session identity). Per the spec, the UE locally releases that PDU session. After the local release, the REF does not send a Registration request to synchronize the PDU session state between the UE and the network. The DUT, in order to align the PDU session state between the UE and the network, sends a Registration request marking that PDU session as inactive. Per the spec, "The UE shall include the PDU session status IE in the Registration request message if there are PDU sessions associated with the 5GS services and which are locally released by the UE", so we send the Registration request. Here an interpretation question arises: if the network has explicitly rejected with Invalid PDU session ID, is the UE supposed to send a Registration request after the local release, or not? The REF does not perform the above behavior — the reasoning being that the network has already rejected that PDU session as invalid, so no additional sync-up is needed.
