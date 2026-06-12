# [RAN1] UCI bit construction when subband PMI and layer indicator are configured

- date: 2025-06-02 09:14:27
- author: anonymous
- category: RAN1(Physical) > UL Control Channel
- Source: internal engineering board (anonymized).

## Body

Hello.

I would like to ask how the UCI bits are constructed when subband PMI and layer indicator are configured together in ReportQuantity in CSI part 2.

In Table 6.3.2.1.2-4 of 38.212, when the layer indicator is configured for the CSI part 2 wideband PMI, it is constructed in the order of Layer Indicator, PMI. I am wondering in what order it is constructed in the subband PMI configuration.

In Table 6.3.2.1.2-5, the construction table for 'CSI report #n Part 2 subband' only has the order mapping for odd and even of the subband PMI, so I am wondering what the mapping order of the layer indicator is in this case.

## Comments (1)

### [1] anonymous — 2025-06-18 15:23

Hello,

Regarding the case you mentioned, "the case where subband PMI and layer indicator are configured together in reportQuantity in CSI part 2", since PMI is configured to be reported per subband, wideband + subband reporting is performed. Therefore, it is correct that both Table 6.3.2.1.2-4 and 6.3.2.1.2-5 are reported, and the reporting position of the Layer Indicator is determined according to Table 6.3.2.1.2-4.

Thank you.
