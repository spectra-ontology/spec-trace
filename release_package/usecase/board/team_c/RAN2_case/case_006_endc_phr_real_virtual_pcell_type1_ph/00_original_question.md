# Case-006 (RAN2) — Basis for Deriving the PCell Type1 PH Value When Transmitting Real/Virtual PHR in EN-DC

> Source: internal engineering board (anonymized).
> WG / Spec domain: 3GPP RAN2 (MAC — Power Headroom Report; EN-DC multiple PHR, real/virtual, phr-ModeOtherCG). Due to the nature of EN-DC, there is a cross-spec association with LTE MAC (TS 36.321).
> Spec: TS 38.321 (NR MAC)
> Case number: RAN2 case-006

---

## Question Body (verbatim — the answering session sees only this question and judges autonomously)

Hello, I have a question regarding Real/Virtual PHR transmission in EN-DC.

When the NR PHR config is defined as below,

```
phr-Config: setup (1)
  setup
    phr-PeriodicTimer: sf100 (3)
    phr-ProhibitTimer: sf50 (3)
    phr-Tx-PowerFactorChange: dB3 (1)
    ...1 ....  multiplePHR: True
    .... 0...  dummy: False
    .... .0..  phr-Type2OtherCell: False
    phr-ModeOtherCG: real (0)
```

I have a question about the PCell Type1 PH for NR multiple PHR. I understand that it maps to the standard text below,

```
4> if this MAC entity has UL resources allocated for transmission on this Serving Cell; or
4> if the other MAC entity, if configured, has UL resources allocated for transmission on this
   Serving Cell and phr-ModeOtherCG is set to real by upper layers:
  5> obtain the value for the corresponding PCMAX,f,c field from the physical layer.
```

In this case, please confirm whether the PH value should also use the real PH value based on LTE's most recently transmitted PUSCH.
