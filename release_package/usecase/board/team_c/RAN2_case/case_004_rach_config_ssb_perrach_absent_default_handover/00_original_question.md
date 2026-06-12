# Case-004 (RAN2) — UE behavior when ssb-perRACH-OccasionAndCB-PreamblesPerSSB is absent in a handover RACH config

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN2 (RRC — RACH configuration / handover; reconfigurationWithSync). Due to the nature of the topic, this is cross-WG into RAN1 PHY (RACH occasion / preamble↔SSB mapping).
> Spec: TS 38.331 (RRC), related RAN1 PHY
> Case number: RAN2 case-004

---

## Question body (verbatim — the answering session sees only this question and reasons autonomously)

Hello. I have a question about UE behavior when, for a handover in SA mode, the following RACH config is received.

```
spCellConfig
  reconfigurationWithSync
    ...
    rach-ConfigCommon: setup (1)
      setup
        rach-ConfigGeneric
          prach-ConfigurationIndex: 79
          msg1-FDM: four (2)
          msg1-FrequencyStart: 0
          zeroCorrelationZoneConfig: 15
          preambleReceivedTargetPower: -92 dBm
          preambleTransMax: n100 (9)
          powerRampingStep: dB4 (2)
          ra-ResponseWindow: sl20 (5)
        ra-ContentionResolutionTimer: sf64 (7)
        rsrp-ThresholdSSB: SS-RSRP < -156dBm (0)
        prach-RootSequenceIndex: l139 (1)
          l139: 0
        msg1-SubcarrierSpacing: kHz30 (1)
        restrictedSetConfig: unrestrictedSet (0)
        dummy: infinity (7)
        ssb-PositionsInBurst: mediumBitmap (1)
          mediumBitmap: 40 [bit length 8, 0100 0000 decimal value 64]
```

1. Since `totalNumberOfRA-Preambles` is absent, it is set to 64.

2. `ssb-perRACH-OccasionAndCB-PreamblesPerSSB` is also absent. In this case, since the `ssb-PositionsInBurst` information indicates that only 1 SSB exists, I would like to ask whether it is acceptable to operate by setting it to `one, n64`.

```
one ENUMERATED {n4,n8,n12,n16,n20,n24,n28,n32,n36,n40,n44,n48,n52,n56,n60,n64}
```

I was not able to find a part that explicitly specifies the UE decision corresponding to point 2 above. Should I consider this to be logically the obvious behavior? Or should I consider that the following RRC spec sentence covers the behavior in point 2?

> The setting should be consistent with the setting of ssb-perRACH-OccasionAndCB-PreamblesPerSSB

I would appreciate an answer regarding point 2. Thank you.
