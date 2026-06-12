# Case-009 — NR-NTN ReferenceLocation (Ellipsoid-Point) degreesLongitude: ASN.1 PER "n–lb" vs 3GPP 2's complement decoding interpretation conflict

> Source: internal engineering board (anonymized). Real engineering question from day-to-day standards work (translated from the Korean original; question content preserved verbatim in meaning)
> WG / Spec domain: RAN2 RRC (TS 38.331 `ReferenceLocation-r17`) + location shape definition (TS 37.355 `Ellipsoid-Point`, TS 23.032 §6.1) + RAN5 conformance (TS 38.523-1 §8.1.4.4.7, TS 38.508-1, TS 36.509) + ITU-T X.691 (PER). The exact spec sources are confirmed against the corpus when the SPECTRA answer is generated.
> Case number: case-009

---

## Question body (preserved verbatim in meaning)

Hello. I have a question about ReferenceLocation, an RRC field related to NR-NTN. ReferenceLocation is of type Ellipsoid-Point and is divided into the following three parts; among these, degreesLongitude is specified as being stored in 2's complement form with the MSB as the sign bit. The content given in §8.1.4.4.7 of the RAN5 test spec (38.523-1) is also based on this. However, in ASN.1, degreesLongitude is defined to be encoded using the "n" – "lb" method, so we are currently encoding/decoding differently from the 3GPP spec. From the UE's perspective, the ASN.1 and 3GPP interpretations differ, which is causing confusion, so I am asking this question. Thank you.

### When decoding degreesLongitude within ReferenceLocation (Ellipsoid-Point)

- ASN.1 behavior: (0x000000 ~ 0xFFFFFF) => (-8,388,608 ~ 8,388,607)
- 3GPP interpretation:
  - (0x000000 ~ 0x7FFFFF) => (0 ~ 8388607)
  - (0x800000 ~ 0xFFFFFF) => (-8388608 ~ -1)

### ASN.1 "n" – "lb" (X.691 11.5.6)

> In the case of the UNALIGNED variant the value ("n" – "lb") shall be encoded as a non-negative-binary-integer in a bit-field as specified in 11.3 with the minimum number of bits necessary to represent the range.

### (3GPP 38.331) – ReferenceLocation

> The IE ReferenceLocation contains location information used as a reference location. The value of the field is same as Ellipsoid-Point defined in TS37.355 [49]. The first/leftmost bit of the first octet contains the most significant bit.

```
ReferenceLocation information element
-- ASN1START
-- TAG-REFERENCELOCATION-START
ReferenceLocation-r17 ::= OCTET STRING
-- TAG-REFERENCELOCATION-STOP
-- ASN1STOP
```

### (3GPP 37.355) Ellipsoid-Point

> The IE Ellipsoid-Point is used to describe a geographic shape as defined in TS 23.032 [15].

```
Ellipsoid-Point ::= SEQUENCE {
   latitudeSign      ENUMERATED {north, south},
   degreesLatitude   INTEGER (0..8388607),      -- 23 bit field
   degreesLongitude  INTEGER (-8388608..8388607) -- 24 bit field
}
```

### (3GPP 23.032) 6.1 Point

> The co-ordinates of an ellipsoid point are coded with an uncertainty of less than 3 metres. The latitude is coded with 24 bits: 1 bit of sign and a number between 0 and 2^23-1 coded in binary on 23 bits. The relation between the coded number N and the range of (absolute) latitudes X it encodes is the following (X in degrees): except for N=2^23-1, for which the range is extended to include N+1.
>
> The longitude, expressed in the range -180°, +180°, is coded as a number between -2^23 and 2^23-1, coded in 2's complement binary on 24 bits. The relation between the coded number N and the range of longitude X it encodes is the following (X in degrees): ...

### (38.523-1) 8.1.4.4.7 — NR NTN / Conditional handover / Success / CondEventD1

Table 8.1.4.4.7.3.3-8: ReportConfigNR-condEventD1 (derivation path TS 38.508-1 [4] Table 4.6.3-142)

```
ReportConfigNR ::= SEQUENCE {
  reportType CHOICE {
    condTriggerConfig-r16 SEQUENCE {
      condEventId CHOICE {
        condEventD1-r17 SEQUENCE {
          distanceThreshFromReference1-r17  2400          -- threshold 1: 120 km
          distanceThreshFromReference2-r17  2400          -- threshold 2: 120 km
          referenceLocation1-r17  '2240 DC56 7176'H       -- reference location 1: Latitude 24.08439333, Longitude 121.56076999
          referenceLocation2-r17  '2519 0956 7176'H       -- reference location 2: Latitude 26.08439333, Longitude 121.56076999
          hysteresisLocation-r17  0
          timeToTrigger-r17       ms2560
        }
      }
    }
  }
}
```

Table 8.1.4.4.7.3.3-9: UPDATE UE LOCATION INFORMATION (Steps 4 and 9; derivation path TS 36.509 [8] Table 6.12)

```
ellipsoidPointWithAltitude  '2519 0956 7176 0000'H   -- UE Location: Latitude 26.08439333, Longitude 121.56076999, Altitude 0   (Step 4)
                            '2240 DC56 7176 0000'H   -- UE Location: Latitude 24.08439333, Longitude 121.56076999, Altitude 0   (Step 9)
horizontalVelocity          '00 0000'H               -- Speed: 0 km/s
gnss-TOD-msec               '00 0000'H
```
