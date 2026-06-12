# SPECTRA answer — UE behavior when ssb-perRACH-OccasionAndCB-PreamblesPerSSB is absent in a handover RACH config

> Regenerated via the SPECTRA retrieval pipeline.
> Question source: `00_original_question.md`

---

## Conclusion (summary)

1. **Point 1 (totalNumberOfRA-Preambles absent → 64) is correct.** This field is one whose behavior upon being absent is explicitly specified (Need S), and the TS 38.331 field description directly states "If the field is absent, all 64 preambles are available for RA".
2. **Point 2 (treating it as "one, n64") is not a behavior specified by the standard.** Your statement that you "could not find a part that explicitly specifies it" reflects the accurate state of affairs — within the scope of what we compared in TS 38.331 (IE definition, field description, signalling conventions), TS 38.321 §5.1.1/5.1.2, and TS 38.213 §8.1, **there is no provision that sets a default value for this field when it is absent.** What the standard actually specifies for the absent case is not a default value but **"maintain the current value" (Need M).**
3. **The sentence you quoted, "The setting should be consistent with the setting of ssb-perRACH-OccasionAndCB-PreamblesPerSSB", does not cover the behavior in point 2.** This sentence is a **network configuration guideline** found in the field description of totalNumberOfRA-Preambles ("should" — configure the two field values so they are mutually consistent); it is not a rule instructing the UE to derive a value when ssb-perRACH-OccasionAndCB-PreamblesPerSSB is absent.

## 1. What the standard specifies for the absent case — Need M ("maintain the current value")

ASN.1 definition (TS 38.331, RACH-ConfigCommon):

```asn1
RACH-ConfigCommon ::= SEQUENCE {
    rach-ConfigGeneric            RACH-ConfigGeneric,
    totalNumberOfRA-Preambles     INTEGER (1..63)    OPTIONAL,  -- Need S
    ssb-perRACH-OccasionAndCB-PreamblesPerSSB CHOICE {
        oneEighth  ENUMERATED {n4,n8,...,n64},
        ...
        one        ENUMERATED {n4,n8,...,n64},
        ...
    }                                                OPTIONAL,  -- Need M
    ...
```

The fact that the two fields have different need codes is the crux of this question. TS 38.331 §6.1.2 (need code definitions):

> "**Need S** — Specified: Used for (configuration) fields, whose field description or procedure **specifies the UE behavior performed upon receiving a message with the field absent**"
>
> "**Need M** — Maintain: Used for (configuration) fields that are stored by the UE i.e. not one-shot. Upon receiving a message with the field absent, **the UE maintains the current value**."

- totalNumberOfRA-Preambles = **Need S** → the field description explicitly states the behavior when absent ("If the field is absent, all 64 preambles are available for RA") → this is why point 1 is correct.
- ssb-perRACH-OccasionAndCB-PreamblesPerSSB = **Need M** → the standard meaning of "absent" is not "apply a default value" but **"maintain the current (currently applied) value".** And the field description of this field contains no sentence specifying behavior when absent (result of comparing the full field description text).

That is, if this field is absent in a handover (reconfigurationWithSync) message, then per the standard's wording the UE **maintains the value it was already applying** on that configuration path (the rach-ConfigCommon of the initial UL BWP). If there is not even a prior value to maintain, then — as in §3 below — it becomes an area where the standard does not define the behavior.

## 2. Why "1 SSB → derive 'one'" and "totalNumber 64 → derive 'n64'" is not a standard rule

- **TS 38.213 §8.1 describes this value only on the premise that it is "provided"**: "For Type-1 random access procedure, a UE **is provided** a number of SS/PBCH block indexes associated with one PRACH occasion and a number of contention based preambles per SS/PBCH block index per valid PRACH occasion **by ssb-perRACH-OccasionAndCB-PreamblesPerSSB**..." — across the full text of §8.1 there is no fallback sentence for when this parameter is not provided (in contrast to other parameters in the same clause, such as ssb-PositionsInBurst and tdd-UL-DL-ConfigurationCommon, which do have an explicit "if a UE is not provided ..." fallback).
- **TS 38.321 §5.1.2 (Random Access Resource selection) likewise presumes that the mapping is defined**, stating only "select a Random Access Preamble randomly with equal probability from the Random Access Preambles **associated with the selected SSB** and the selected Random Access Preambles group". There is no branch for the case where the association itself does not exist.
- This field carries **two pieces of information simultaneously**: a CHOICE (SSB/RO ratio) and an ENUMERATED (number of CB preambles per SSB) (38.331 field description: "The meaning of this field is twofold... The total number of CB preambles in a RACH occasion is given by CB-preambles-per-SSB * max(1, SSB-per-rach-occasion)"). What can be derived from ssb-PositionsInBurst is at most the fact that "1 SSB is transmitted", and **the number of CB preambles per SSB (n4~n64) is not derivable from any configuration field**. "n64" is a combination of additional assumptions — totalNumberOfRA-Preambles absent (→64) + all used for CB + group B not configured — not a standard rule.

## 3. So how should the UE actually behave

A summary faithful to the standard's wording is as follows.

1. **When there is a prior applied value (the normal handover case)**: maintain the prior value as per the Need M wording. However, since this means the source configuration's value is applied as-is to the target cell, if the target cell's SSB/RACH configuration differs from the source, the network leaving this field absent is itself a configuration quality problem (which is why, in actual network deployments, it is common to explicitly specify this field).
2. **When there is no value to maintain**: this is a standard-undefined area. Since the 38.213 §8.1 mapping does not hold, a UE assuming "one, n64" and operating on that basis is a **defensive implementation choice**, not something for which there is a basis to claim it is standard-compliant behavior. For reference, in configuration via system information, per the rule in 38.331 §6.1.2 that "Any field with Need M or Need N **in system information** shall be interpreted as **Need R**", absent = release (not configured); this too is "not configured", not "default value" — i.e., nowhere in the standard is there an implicit default value for this field.
3. **A practical answer for the question's scenario**: a case like the config you provided, where rach-ConfigCommon comes as setup but this field is absent, should not be treated as "may the UE operate as one/n64 on its own?" but rather **as a case where a field the network was supposed to fill in is missing, and (if this is a test/IOT stage) the standard-consistent response is to request the network side to complete the configuration.** A UE implementation operating under the assumption of 1 SSB for robustness purposes is not itself prohibited, but that behavior is not justified by a spec citation.

## 4. Why the question's RRC quote does not cover this (reconfirmation)

The full original text of the sentence you quoted (TS 38.331, totalNumberOfRA-Preambles field description):

> "Total number of preambles used for contention based and contention free 4-step or 2-step random access in the RACH resources defined in RACH-ConfigCommon, excluding preambles used for other purposes (e.g. for SI request). **If the field is absent, all 64 preambles are available for RA.** The setting should be consistent with the setting of ssb-perRACH-OccasionAndCB-PreamblesPerSSB, **i.e. it should be a multiple of the number of SSBs per RACH occasion.**"

The subject of this sentence is the "setting" of totalNumberOfRA-Preambles (the value the network decides), and what it requires is an **inter-configuration consistency constraint** ("the total number of preambles should be a multiple of the number of SSBs per RO"). Since it is not a sentence granting the UE a procedure for determining a value when ssb-perRACH-OccasionAndCB-PreamblesPerSSB is absent, it cannot serve as the basis clause for the behavior in point 2.

## Verification scope and limitations

- Scope of comparison: the full TS 38.331 RACH-ConfigCommon ASN.1 / field description, §6.1.2 (need code definitions), §6.1.3 (general rules), §5.3.5.5.2 (reconfiguration with sync), Annex A.3.8/A.6; the full text of TS 38.321 §5.1.1/5.1.2; the full text of TS 38.213 §8.1. Within this scope we confirmed the absence of any provision defining a default value when absent, and web public-source cross-checking yielded the same.
- The handling of "when there is no prior value to maintain" (whether to treat the absence of a Need M field inside an IE newly constructed via setup as maintaining the source value or as not configured) is an interpretation area that is not fully closed by the 38.331 convention wording alone, and this answer honestly marks it as "standard-undefined". We did not find any RAN2 agreement document or CR that explicitly closes this point within the scope of the meeting documents we hold (RAN2 TDoc/CR).
- The validity of the other fields in the received config (prach-ConfigurationIndex 79, etc.) is outside the scope of this question and was not verified.
