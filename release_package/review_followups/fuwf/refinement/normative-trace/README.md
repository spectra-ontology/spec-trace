# One original-source normative trace: R1-2210700 / CR0388

The fixed named example was chosen before fetching its normative versions. It is a documentary follow-up to an already inspected example, not an additional random sample or a post-hoc estimate of SPECTRA accuracy. Only native ZIP/DOCX OOXML was read; no database, production parser, generated SPECTRA answer, external model, or graph mutation was used.

The WG110bis-e meeting report explicitly agrees final CR R1-2210700, identifying TS38.213, base version17.3.0, Rel17 and CR0388. The native CR cover identifies clause18. Its single tracked paragraph inserts a restriction on providing the semi-static multicast HARQ-ACK codebook in the second reporting mode. That complete inserted sentence has zero exact paragraph and normalized full-document substring matches in the original v17.3.0, and one exact match in clause18 of original v17.4.0. The two final sentence strings are also equal before whitespace normalization. The v17.4.0 native change-history explicitly lists CR0388, RP-222864, RAN#98-e, December2022 and new version17.4.0.

This supports documentary incorporation of this specific sentence. It does not establish causal motivation, every approval step, corpus-wide relation reliability/completeness, or a KG advantage over another representation.

## Original locators

Indices are zero based in native `word/document.xml`. `paragraph_index` counts top-level body paragraphs only; table rows/cells have separate indices.

| Evidence | Native locator |
|---|---|
| WG report agreement naming final R1-2210700 | body2272 / top-level paragraph2231 |
| WG CR specification, CR number, base version | body2 / table0 / row3 / cells1,3,7 |
| WG CR clauses affected | body6 / table2 / row17 / cell1 / cell paragraph0 |
| WG CR tracked inserted sentence | body17 / top-level paragraph14; six insertion runs, zero deletion runs, empty pre-insertion text |
| v17.3.0 clause18 heading | body4136 / top-level paragraph4038 |
| v17.3.0 unchanged CR-context neighbors, adjacent with no inserted sentence | body4158 and4159 / top-level paragraphs4060 and4061 |
| v17.4.0 clause18 heading | body4162 / top-level paragraph4064 |
| v17.4.0 inserted sentence, no tracked insertion/deletion remaining | body4175 / top-level paragraph4077 |
| v17.4.0 CR0388 change-history row | body4240 / table78 / row352 / cells0–7 |
| RP-222864 native CR member tracked insertion | body17 / top-level paragraph14 |

The short exact sentence excerpt retained for sharing is: “the UE does not expect to be provided pdsch-HARQ-ACK-Codebook = semi-static for multicast HARQ-ACK information.” The complete paragraph is used for the comparison; its digest and full local verification context are retained separately.

## Official sources and pins

| Native source | Official archive | Archive SHA256 | Native DOCX SHA256 |
|---|---|---|---|
| Meeting report | [WG110bis-e report](https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_110b-e/Report/Final_Minutes_report_RAN1%23110b-e_v100.zip) | `33b93234e9303ad7a0b361f0938f6f5aaf61f93fb7208609aa2a4b05dc37b1ff` | `ded5c81f3d9cf38a97696845d1d81cd57cb076ce5a7e8fc9e40396c2280fc38d` |
| WG CR | [R1-2210700](https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_110b-e/Docs/R1-2210700.zip) | `3734cebc72046e55f8d98ca28fc5ed2b5006d97904bca6ef1765e9391ff0e6ea` | `8a48c0c96d07020893c7c7bf49e48aa88becc055dfb6fb83e10fd8aedc8cde73` |
| Earlier TS | [38.213 v17.3.0](https://www.3gpp.org/ftp/Specs/archive/38_series/38.213/38213-h30.zip) | `e1a872ecc25a19b4640085952eef8be296cbaed48c93a6c393cc8aa575d2ec96` | `f46c2a50d6eb6f2d77528e0cb94d124b878eaa7071535fddb290a29d0700b432` |
| Subsequent TS | [38.213 v17.4.0](https://www.3gpp.org/ftp/Specs/archive/38_series/38.213/38213-h40.zip) | `3a5101703ff74a857a090ac74156e6557cf9f1929051207b1196475322416ea3` | `6321accab068f9369cce31dc1af38d77e6ce5bcae060fc78603c874771393458` |
| TSG CR pack | [RP-222864](https://www.3gpp.org/ftp/tsg_ran/TSG_RAN/TSGR_98e/Docs/RP-222864.zip) | `f3e0f1428b536577e1769ebe0460fe34804de90d476e655b8457905c86526279` | `9795fb7c36a7294b4850e433b079686e832081c588191207bed2b86506b52c44` |

The first two official archives were externally byte-verified in the existing sibling `external-source-examples/verification.json`; this reader pins the same archive bytes. Both normative versions and the RP pack were downloaded from their official URLs with HTTP200. The RP download is exactly equal to the retained local ZIP. All pinned local inputs remained unchanged across reads.

The RP pack contains `38213_CR0388_(Rel-17)_R1-2210700.docx`. Its native DOCX and main XML bytes differ from the WG member, so byte equivalence is not claimed. All121 visible main-document paragraphs match exactly in both final and before-revision text; the same cover fields and tracked insertion are present. Formatting, comments, headers, footers, properties and author identity were not compared. The binary `RP-222864_cover.doc` was hashed but not decoded. The derivative local `cr_list.csv` row is preserved as non-primary metadata and is not used as original approval evidence.

## Artifacts and execution

`evidence-excerpt.json` contains field-sized excerpts, source/member hashes, exact locators and limitations, using relative paths only. It contains no full native source, model answer, host absolute path or new graph result. Downloaded native ZIPs are retained for local verification; they are not included by this reader in a final supplement. `verified-trace.json` and `inspection.json` retain local reading context. `rp-member-verification.json` and `rp-difference-check.json` explicitly distinguish native bytes from visible text.

Four bounded guard runs completed with exit0. Every run used the unchanged project guard, MemoryMax2GiB, MemoryHigh1GiB, zero cgroup swap, TasksMax64, CPU0–1, and the Windows/WSL16GiB reserve. Maximum observed memory peak across these runs was224,661,504bytes; OOM, memory-high and memory-max events were zero. The guard logs are `guard/`, `guard-verification/`, `guard-export/` and `guard-rp-difference/`. Reader code is preserved as `producer.py`, `verify_trace.py`, `export_excerpt.py` and `rp_difference_check.py`.

Suggested reply wording: “For one concrete, source-verifiable trace, the WG110bis-e minutes agree R1-2210700/CR0388; its native CR inserts a clause18 sentence that is absent from TS38.213v17.3.0 and appears verbatim in v17.4.0, whose native change-history explicitly records CR0388 under RP-222864. This establishes documentary traceability for that sentence; we report it alongside the bounded relation audit rather than generalizing it to corpus-wide accuracy or causal attribution.”
