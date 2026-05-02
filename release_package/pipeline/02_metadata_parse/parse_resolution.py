"""SPECTRA pipeline — Stage 02b: parse Resolution from chairman notes to JSON-LD.

Reads chairman notes (DOCX) for a meeting and emits SPECTRA-conformant JSON-LD
records for Resolution instances (Agreement / Conclusion / WorkingAssumption).

Sanitized for public release.

Usage:
    python parse_resolution.py --meeting RAN1#84 --notes /path/to/ChairmanNotes.docx --out resolutions.jsonld
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any

from docx import Document

SPECTRA = "https://w3id.org/spectra#"

# Resolution-type keyword detection in chairman-notes paragraphs
RES_KEYWORDS = {
    "Agreement": [
        r"^\s*Agreement\s*:",
        r"^\s*Agreed\s*:",
        r"^\s*Decision\s*:\s*Agreed",
    ],
    "Conclusion": [
        r"^\s*Conclusion\s*:",
        r"^\s*Concluded\s*:",
    ],
    "WorkingAssumption": [
        r"^\s*Working\s+[Aa]ssumption\s*:",
        r"^\s*WA\s*:",
    ],
}


def detect_resolution_type(paragraph_text: str) -> str | None:
    """Returns Agreement / Conclusion / WorkingAssumption or None."""
    for cls, patterns in RES_KEYWORDS.items():
        for pat in patterns:
            if re.match(pat, paragraph_text):
                return cls
    return None


def extract_referenced_tdocs(text: str) -> List[str]:
    """TDoc numbers cited inside resolution text (e.g., 'as in R1-2400001')."""
    pattern = re.compile(r"\b([RSC][P1-6]?-\d{6,7})\b")
    return list(set(pattern.findall(text)))


def detect_agenda_marker(paragraph_text: str) -> str | None:
    """Detect 'Agenda Item 8.4' or '8.4.1' headings (chairman-notes section breaks)."""
    m = re.match(r"^\s*(?:Agenda\s+[Ii]tem\s+)?(\d+(?:\.\d+)+)\b", paragraph_text)
    return m.group(1) if m else None


def parse_chairman_notes(docx_path: Path, meeting: str) -> List[Dict[str, Any]]:
    """Walk DOCX paragraphs, detect resolutions, emit JSON-LD records."""
    doc = Document(str(docx_path))
    current_agenda: str | None = None
    records: List[Dict[str, Any]] = []
    res_count = 0
    for para in doc.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue
        # Track agenda-item context
        agenda = detect_agenda_marker(text)
        if agenda:
            current_agenda = agenda
            continue
        # Detect resolution
        res_type = detect_resolution_type(text)
        if not res_type:
            continue
        res_count += 1
        rec: Dict[str, Any] = {
            "@id": f"{SPECTRA}resolution/{meeting}-{res_count:04d}",
            "@type": f"{SPECTRA}{res_type}",
            f"{SPECTRA}decisionText": text,
            f"{SPECTRA}madeAt": {"@id": f"{SPECTRA}meeting/{meeting}"},
        }
        if current_agenda:
            rec[f"{SPECTRA}resolutionBelongsTo"] = {
                "@id": f"{SPECTRA}agenda/{meeting}-{current_agenda}"
            }
        # references to cited TDocs
        cited = extract_referenced_tdocs(text)
        if cited:
            rec[f"{SPECTRA}references"] = [{"@id": f"{SPECTRA}tdoc/{n}"} for n in cited]
        records.append(rec)
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--meeting", required=True, help="Meeting ID (e.g., RAN1#84)")
    ap.add_argument("--notes", required=True, type=Path, help="Path to chairman-notes DOCX")
    ap.add_argument("--out", required=True, type=Path, help="Output JSON-LD path")
    args = ap.parse_args()

    if not args.notes.exists():
        sys.exit(f"ERROR: Chairman notes not found: {args.notes}")

    records = parse_chairman_notes(args.notes, args.meeting)
    graph = {
        "@context": {"@vocab": SPECTRA, "tdoc": SPECTRA},
        "@graph": records,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(graph, indent=2, ensure_ascii=False))
    print(f"[parse_resolution] Wrote {len(records)} Resolution records to {args.out}")


if __name__ == "__main__":
    main()
