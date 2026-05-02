"""SPECTRA pipeline — Stage 02a: parse TDoc cover-sheet metadata to JSON-LD.

Reads per-meeting TDoc inventory spreadsheets (TDoc_List/*.xlsx) and emits
SPECTRA-conformant JSON-LD records for Tdoc / CR / LS instances.

Sanitized for public release: hard-coded internal paths, monitoring hooks,
and Slack incident wrappers removed. The deterministic parser logic
(prefix→WG inference, type classification, agenda-item normalisation,
cross-record relations) is preserved.

Usage:
    python parse_tdoc_cover.py --meeting RAN1#84 --tdoc-list /path/to/TDoc_List.xlsx --out tdocs.jsonld
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

import pandas as pd

# SPECTRA namespace (matches release_package/ontology/spectra.ttl)
SPECTRA = "https://w3id.org/spectra#"

# Working group prefix → URI inference (per 3GPP TDoc number convention)
WG_PREFIX_MAP = {
    "R1": "RAN1", "R2": "RAN2", "R3": "RAN3", "R4": "RAN4", "R5": "RAN5",
    "RP": "RAN", "S1": "SA1", "S2": "SA2", "S3": "SA3", "S4": "SA4",
    "S5": "SA5", "S6": "SA6", "SP": "SA", "C1": "CT1", "C3": "CT3",
    "C4": "CT4", "C6": "CT6", "CP": "CT",
}

# Type column → SPECTRA class
TYPE_TO_CLASS = {
    "CR": "CR",
    "Liaison Statement": "LS", "LS in": "LS", "LS out": "LS",
    "discussion": "Tdoc", "pCR": "Tdoc", "draftCR": "Tdoc",
    "Report": "Tdoc", "WID new": "Tdoc", "WID revised": "Tdoc",
    "SID new": "Tdoc", "SID revised": "Tdoc",
    "TS or TR cover": "Tdoc", "draft TS": "Tdoc", "draft TR": "Tdoc",
    "agreement": "Tdoc", "session notes": "SessionNotes",
    "summary": "Summary", "executable code": "Tdoc", "other": "Tdoc",
}


def infer_wg_from_tdoc_number(tdoc_number: str) -> str | None:
    """Extract WG from TDoc number prefix (e.g., R1-2400001 → RAN1)."""
    m = re.match(r"^([A-Z]+\d?)-", tdoc_number)
    if not m:
        return None
    prefix = m.group(1)
    return WG_PREFIX_MAP.get(prefix)


def classify_tdoc_type(type_field: str) -> str:
    """Classify TDoc Type column into SPECTRA class (Tdoc/CR/LS/Summary/SessionNotes)."""
    if not type_field:
        return "Tdoc"
    cls = TYPE_TO_CLASS.get(type_field.strip())
    return cls if cls else "Tdoc"


def normalise_agenda(meeting: str, agenda_item: str) -> str:
    """Composite agenda key: tdoc:agenda/{meeting}-{agenda} (e.g., RAN1#84-7.1)."""
    if not agenda_item:
        return ""
    return f"{SPECTRA}agenda/{meeting}-{agenda_item}"


def parse_company_field(source_field: str) -> List[str]:
    """Source column → company URIs. Multi-author TDocs are comma- or
    semicolon-separated; preserved verbatim per public TDoc cover sheets.
    """
    if not source_field:
        return []
    companies = re.split(r"[,;]\s*", source_field.strip())
    return [f"{SPECTRA}company/{c.replace(' ', '_')}" for c in companies if c]


def parse_cr_affect_flags(row: Dict[str, Any]) -> Dict[str, bool]:
    """CR affect flags from Boolean columns (affectsUICC/ME/RAN/CN)."""
    return {
        f"{SPECTRA}affects{slot}": bool(row.get(f"affects{slot}", False))
        for slot in ("UICC", "ME", "RAN", "CN")
    }


def parse_tdoc_row(row: Dict[str, Any], meeting: str) -> Dict[str, Any]:
    """Parse one TDoc inventory row into a SPECTRA JSON-LD record."""
    tdoc_num = row.get("TDoc", "").strip()
    type_field = row.get("Type", "").strip()
    cls = classify_tdoc_type(type_field)
    record = {
        "@id": f"{SPECTRA}tdoc/{tdoc_num}",
        "@type": f"{SPECTRA}{cls}",
        f"{SPECTRA}tdocNumber": tdoc_num,
        f"{SPECTRA}title": row.get("Title", "").strip(),
        f"{SPECTRA}submittedBy": parse_company_field(row.get("Source", "")),
        f"{SPECTRA}presentedAt": [{"@id": f"{SPECTRA}meeting/{meeting}"}],
    }
    wg = infer_wg_from_tdoc_number(tdoc_num)
    if wg:
        record[f"{SPECTRA}submittedToWG"] = {"@id": f"{SPECTRA}wg/{wg}"}
    agenda = normalise_agenda(meeting, row.get("Agenda item", "").strip())
    if agenda:
        record[f"{SPECTRA}belongsTo"] = {"@id": agenda}
    if cls == "CR":
        record.update(parse_cr_affect_flags(row))
    # Cross-record relations (revision chains, LS reply chains)
    for rel_field, rel_pred in [
        ("Revision of", "isRevisionOf"),
        ("Revised to", "revisedTo"),
        ("Reply to", "replyTo"),
        ("Reply in", "replyIn"),
    ]:
        ref = row.get(rel_field, "").strip()
        if ref:
            record[f"{SPECTRA}{rel_pred}"] = {"@id": f"{SPECTRA}tdoc/{ref}"}
    return record


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meeting", required=True, help="Meeting ID (e.g., RAN1#84)")
    ap.add_argument("--tdoc-list", required=True, type=Path, help="Path to TDoc_List.xlsx")
    ap.add_argument("--out", required=True, type=Path, help="Output JSON-LD path")
    args = ap.parse_args()

    if not args.tdoc_list.exists():
        sys.exit(f"ERROR: TDoc list not found: {args.tdoc_list}")

    df = pd.read_excel(args.tdoc_list, dtype=str).fillna("")
    records: List[Dict[str, Any]] = [parse_tdoc_row(row.to_dict(), args.meeting) for _, row in df.iterrows()]

    graph = {
        "@context": {"@vocab": SPECTRA, "tdoc": SPECTRA},
        "@graph": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    print(f"[parse_tdoc_cover] Wrote {len(records)} TDoc records to {args.out}")


if __name__ == "__main__":
    main()
