#!/usr/bin/env python3
"""SPECTRA Stage 01 - Reference TDoc & document extractor.

Fetches a 3GPP meeting folder listing from the public 3GPP FTP portal,
downloads its TDoc spreadsheet, and (optionally) walks the meeting
attachments list to fetch CR / TR / TS document binaries used by later
pipeline stages.

This is a *reference* implementation:

* it shows the URL conventions the rest of the pipeline assumes,
* it is deterministic and inspectable,
* it deliberately omits any corporate proxy / SSO / monitoring glue that
  was used internally to fetch the SPECTRA v1.0.0 corpus.

Reusers must respect the 3GPP terms of use and rate limits and supply
their own credentials / retry policy where needed.

Inputs (CLI):
    --meeting-url     Full URL of a 3GPP meeting folder, e.g.
                      https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_104b-e/
    --working-group   RAN1 / RAN2 / RAN3 / RAN4 / RAN5

Outputs:
    ${SPECTRA_DATA_DIR}/<WG>/TDoc_List/*.xlsx
    ${SPECTRA_DATA_DIR}/<WG>/<docs...>
"""
from __future__ import annotations

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

LOG = logging.getLogger("spectra.extract")

DEFAULT_TIMEOUT = 60  # seconds
DEFAULT_RATE_LIMIT_SLEEP = 1.0  # seconds between requests

XLSX_RE = re.compile(r"\.xlsx?$", re.IGNORECASE)
DOCX_RE = re.compile(r"\.docx?$", re.IGNORECASE)
ZIP_RE = re.compile(r"\.zip$", re.IGNORECASE)


def data_root() -> Path:
    """Return the corpus root directory (SPECTRA_DATA_DIR or ./spectra-corpus)."""
    root = os.environ.get("SPECTRA_DATA_DIR")
    if root:
        return Path(root).expanduser().resolve()
    return Path("./spectra-corpus").resolve()


def fetch_html(url: str, session: requests.Session) -> str:
    """Fetch a directory listing as HTML. Raises on HTTP error."""
    resp = session.get(url, timeout=DEFAULT_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def list_directory(url: str, session: requests.Session) -> list[str]:
    """Parse a 3GPP FTP directory listing and return absolute child URLs."""
    html = fetch_html(url, session)
    soup = BeautifulSoup(html, "html.parser")
    children: list[str] = []
    for a in soup.find_all("a"):
        href = a.get("href")
        if not href:
            continue
        # skip parent / sort links
        if href.startswith("?") or href in ("../", "/"):
            continue
        children.append(urljoin(url, href))
    return children


def download(url: str, dest: Path, session: requests.Session) -> None:
    """Stream-download a binary file to *dest*. Skips if already present."""
    if dest.exists() and dest.stat().st_size > 0:
        LOG.debug("skip (cached): %s", dest)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    LOG.info("download: %s -> %s", url, dest)
    with session.get(url, stream=True, timeout=DEFAULT_TIMEOUT) as resp:
        resp.raise_for_status()
        tmp = dest.with_suffix(dest.suffix + ".part")
        with open(tmp, "wb") as fh:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    fh.write(chunk)
        tmp.replace(dest)


def meeting_id_from_url(meeting_url: str) -> str:
    """Pull the meeting tag (e.g. TSGR1_104b-e) out of a meeting folder URL."""
    path = urlparse(meeting_url).path.rstrip("/")
    return path.rsplit("/", 1)[-1]


def fetch_tdoc_list(meeting_url: str, wg_dir: Path,
                    session: requests.Session) -> list[Path]:
    """Find and download xlsx TDoc spreadsheets from the meeting folder.

    Returns the list of downloaded local paths.
    """
    meeting_id = meeting_id_from_url(meeting_url)
    tdoc_dir = wg_dir / "TDoc_List"
    tdoc_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    # Many meetings expose TDoc lists either at the root or in an Inbox
    # subdirectory. Walk the listing once and capture spreadsheets.
    for child in list_directory(meeting_url, session):
        name = urlparse(child).path.rsplit("/", 1)[-1]
        if not XLSX_RE.search(name):
            continue
        dest = tdoc_dir / f"{meeting_id}_{name}"
        download(child, dest, session)
        time.sleep(DEFAULT_RATE_LIMIT_SLEEP)
        saved.append(dest)
    return saved


def fetch_documents(meeting_url: str, wg_dir: Path,
                    session: requests.Session, max_docs: int | None = None) -> int:
    """Walk Docs/ subdirectory and download .docx / .zip attachments.

    Returns the count of files downloaded (including cached skips).
    """
    docs_url = urljoin(meeting_url + "/", "Docs/")
    try:
        children = list_directory(docs_url, session)
    except requests.HTTPError as exc:
        LOG.warning("no Docs/ listing at %s: %s", docs_url, exc)
        return 0

    docs_dir = wg_dir / "documents" / meeting_id_from_url(meeting_url)
    count = 0
    for child in children:
        name = urlparse(child).path.rsplit("/", 1)[-1]
        if DOCX_RE.search(name) or ZIP_RE.search(name):
            dest = docs_dir / name
            download(child, dest, session)
            count += 1
            time.sleep(DEFAULT_RATE_LIMIT_SLEEP)
            if max_docs is not None and count >= max_docs:
                break
    return count


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--meeting-url", required=True,
                   help="3GPP meeting folder URL, e.g. "
                        "https://www.3gpp.org/ftp/tsg_ran/WG1_RL1/TSGR1_104b-e/")
    p.add_argument("--working-group", required=True,
                   choices=["RAN1", "RAN2", "RAN3", "RAN4", "RAN5"],
                   help="Working group label used for the local directory layout.")
    p.add_argument("--max-docs", type=int, default=None,
                   help="Optional cap on how many attachments to fetch.")
    p.add_argument("--skip-documents", action="store_true",
                   help="Only download the TDoc list spreadsheet(s).")
    p.add_argument("-v", "--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    wg_dir = data_root() / args.working_group
    wg_dir.mkdir(parents=True, exist_ok=True)
    LOG.info("output root: %s", wg_dir)

    session = requests.Session()
    # Reusers may inject their own auth here (e.g. session.auth = ...).

    saved = fetch_tdoc_list(args.meeting_url, wg_dir, session)
    LOG.info("TDoc lists downloaded: %d", len(saved))

    if not args.skip_documents:
        n_docs = fetch_documents(args.meeting_url, wg_dir, session,
                                 max_docs=args.max_docs)
        LOG.info("attachments fetched: %d", n_docs)

    return 0


if __name__ == "__main__":
    sys.exit(main())
