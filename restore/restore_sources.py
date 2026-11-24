"""Restore the meeting-report files that the disposition records cite.

The release carries hashes and locators, not report text. This script fetches each cited
report from the public 3GPP archive, rebuilds the cited file and checks its SHA-256.

Usage:
    python3 -I restore/restore_sources.py --manifest sources/manifest.jsonl \
        --dest <release root> --work <empty work directory> [--wg RAN1 ...] [--report out.jsonl]
        [--convert-tmp <folder at most three levels below the file-system root>]

Each manifest row names the archive URL and its SHA-256, the archive member, and how the
cited file is obtained from that member. The archive keeps earlier report versions in a
Report/history/ folder, so a report row lists the other of the two folders under
urlAlternates; the locations are tried in order until one returns the recorded archive hash.
    conversion null              the member (or the downloaded file) is the cited file;
    conversion.method libreoffice   LibreOffice converts the .doc/.rtf member to .docx from and
                                    into the recorded folders (conversion.layout: input and output
                                    folders and the depth of their common root below the
                                    file-system root), which fix the relative hyperlink targets it
                                    writes; the recorded identifiers of embedded OLE objects
                                    (conversion.objectIds) are written back in document order,
                                    and the ZIP entry date/time of the result is set to the
                                    recorded value;
    conversion.method docm-repackage the .docm member is repackaged as .docx: macro parts are
                                    removed, the main content type is set to the plain document
                                    type, and every other part is copied unchanged.
Three checks are recorded per row: archive hash, member hash and cited-file hash. A file is
written under --dest only when its cited hash matches.

Requirements: Python 3 with lxml; LibreOffice for rows whose method is libreoffice.
Downloads are sequential and use a generic User-Agent.
"""
import argparse
import collections
import hashlib
import http.client
import io
import json
import os
import posixpath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
import zlib
from urllib.parse import unquote

USER_AGENT = "Mozilla/5.0 (compatible; restore-sources/1.0)"
RETRIES = 4
PAUSE_SEC = 1.0


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url):
    last = None
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read(), None
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, f"HTTP {e.code}"
            last = f"HTTP {e.code}"
        except (urllib.error.URLError, http.client.HTTPException, OSError) as e:
            last = f"{type(e).__name__}: {e}"
        time.sleep(5 * (attempt + 1))
    return None, last


# ---------------------------------------------------------------- LibreOffice route

def dos_fields(dt):
    y, mo, d, hh, mi, ss = dt
    return (hh << 11) | (mi << 5) | (ss // 2), ((y - 1980) << 9) | (mo << 5) | d


def stamp_zip(data, dt):
    """Set the DOS time/date of every local header and central-directory entry to dt."""
    t, d = dos_fields(dt)
    buf = bytearray(data)
    eocd = data.rfind(b"PK\x05\x06")
    if eocd < 0:
        raise ValueError("no end-of-central-directory record")
    count, _size, cd = struct.unpack_from("<HII", data, eocd + 10)
    pos = cd
    for _ in range(count):
        if data[pos:pos + 4] != b"PK\x01\x02":
            raise ValueError("bad central-directory entry")
        struct.pack_into("<HH", buf, pos + 12, t, d)
        nlen, elen, clen = struct.unpack_from("<HHH", data, pos + 28)
        local = struct.unpack_from("<I", data, pos + 42)[0]
        if data[local:local + 4] != b"PK\x03\x04":
            raise ValueError("bad local header")
        struct.pack_into("<HH", buf, local + 10, t, d)
        pos += 46 + nlen + elen + clen
    return bytes(buf)


def conversion_tree(base, depth):
    """Create a fresh folder exactly `depth` folders below the file-system root, inside base."""
    top = tempfile.mkdtemp(prefix="rs", dir=base)
    have = len(os.path.abspath(top).strip(os.sep).split(os.sep))
    if have > depth:
        shutil.rmtree(top, ignore_errors=True)
        raise RuntimeError(f"--convert-tmp is too deep: the conversion tree must sit {depth} "
                           f"folders below the file-system root")
    root = os.path.join(top, *(["t"] * (depth - have))) if depth > have else top
    os.makedirs(root, exist_ok=True)
    return top, root


def libreoffice_convert(member_name, data, workdir, layout, convert_tmp):
    """LibreOffice stores every hyperlink to a local file as a path relative to the output
    folder, also when the link climbs to the file-system root (for example a drive path in the
    source document). The member is therefore converted from and into the recorded relative
    folders of a fresh tree whose root sits at the recorded depth below the file-system root."""
    top, tree = conversion_tree(convert_tmp, layout["rootDepth"])
    try:
        return _convert(member_name, data, workdir, tree, layout)
    finally:
        shutil.rmtree(top, ignore_errors=True)


def _convert(member_name, data, workdir, tree, layout):
    src_dir, out_dir = safe_dest(tree, layout["input"]), safe_dest(tree, layout["output"])
    profile = os.path.join(workdir, "profile")
    for x in (src_dir, out_dir, profile):
        os.makedirs(x)
    src = os.path.join(src_dir, os.path.basename(member_name))
    with open(src, "wb") as f:
        f.write(data)
    cmd = ["soffice", "--headless", f"-env:UserInstallation=file://{profile}",
           "--convert-to", "docx", "--outdir", out_dir, src]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=900,
                   check=False)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(src))[0] + ".docx")
    if not os.path.exists(out):
        return None
    with open(out, "rb") as f:
        return f.read()


# ---------------------------------------------------------------- OLE object identifiers

OBJECT_ID = re.compile(rb'(ObjectID=")(_\d+)(")')
LO_BLOCK = 128 * 1024


def lo_deflate(plain, blocks):
    """Raw deflate as LibreOffice writes it: level 6 in one stream, or, for large parts, in
    128 KiB blocks, each primed with the preceding 32 KiB and ended by a sync flush."""
    if not blocks:
        c = zlib.compressobj(6, zlib.DEFLATED, -15, 8, 0)
        return c.compress(plain) + c.flush()
    out = []
    for start in range(0, len(plain), LO_BLOCK):
        zd = plain[max(0, start - 32768):start]
        c = zlib.compressobj(6, zlib.DEFLATED, -15, 8, 0, zd) if zd else \
            zlib.compressobj(6, zlib.DEFLATED, -15, 8, 0)
        last = start + LO_BLOCK >= len(plain)
        out.append(c.compress(plain[start:start + LO_BLOCK]) +
                   c.flush(zlib.Z_FINISH if last else zlib.Z_SYNC_FLUSH))
    return b"".join(out)


def _entries(data):
    eocd = data.rfind(b"PK\x05\x06")
    count, cd_size, cd = struct.unpack_from("<HII", data, eocd + 10)
    out, pos = [], cd
    for _ in range(count):
        nlen, elen, clen = struct.unpack_from("<HHH", data, pos + 28)
        out.append({"cd": pos, "cdEnd": pos + 46 + nlen + elen + clen,
                    "name": data[pos + 46:pos + 46 + nlen].decode("utf-8"),
                    "local": struct.unpack_from("<I", data, pos + 42)[0],
                    "csize": struct.unpack_from("<I", data, pos + 20)[0]})
        pos = out[-1]["cdEnd"]
    return out, eocd, cd


def replace_part(data, name, plain, raw):
    """Return the archive with one deflated part replaced; every other byte is kept."""
    entries, eocd, cd = _entries(data)
    by_local = sorted(entries, key=lambda e: e["local"])
    crc, usize, csize = zlib.crc32(plain), len(plain), len(raw)
    body, new_local, pos = [], {}, 0
    for e in by_local:
        start = e["local"]
        if start != pos:
            raise ValueError("unexpected bytes between archive entries")
        nlen, elen = struct.unpack_from("<HH", data, start + 26)
        dstart = start + 30 + nlen + elen
        dend = dstart + e["csize"]
        flags = struct.unpack_from("<H", data, start + 6)[0]
        desc = 0
        if flags & 8:
            desc = 16 if data[dend:dend + 4] == b"PK\x07\x08" else 12
        end = dend + desc
        seg = bytearray(data[start:end])
        if e["name"] == name:
            head = bytearray(data[start:dstart])
            if struct.unpack_from("<I", head, 18)[0] or not flags & 8:
                struct.pack_into("<III", head, 14, crc, csize, usize)
            tail = bytearray(data[dend:end])
            if desc:
                struct.pack_into("<III", tail, desc - 12, crc, csize, usize)
            seg = head + raw + tail
        new_local[e["name"]] = sum(len(b) for b in body)
        body.append(bytes(seg))
        pos = end
    if pos != cd:
        raise ValueError("unexpected bytes before the central directory")
    out = bytearray(b"".join(body))
    new_cd = len(out)
    for e in entries:
        rec = bytearray(data[e["cd"]:e["cdEnd"]])
        if e["name"] == name:
            struct.pack_into("<III", rec, 16, crc, csize, usize)
        struct.pack_into("<I", rec, 42, new_local[e["name"]])
        out += rec
    tail = bytearray(data[eocd:])
    struct.pack_into("<II", tail, 12, len(out) - new_cd, new_cd)
    return bytes(out + tail)


def restore_object_ids(data, recorded):
    """LibreOffice draws the ObjectID of each embedded OLE object at random. The recorded values
    of the cited file are written back in document order, and the part is recompressed the
    way LibreOffice compressed the fresh conversion."""
    z = zipfile.ZipFile(io.BytesIO(data))
    for name, values in recorded.items():
        info = z.getinfo(name)
        plain = z.read(name)
        if len(OBJECT_ID.findall(plain)) != len(values):
            raise ValueError(f"{name}: {len(OBJECT_ID.findall(plain))} OLE objects, "
                             f"{len(values)} recorded")
        nlen, elen = struct.unpack_from("<HH", data, info.header_offset + 26)
        start = info.header_offset + 30 + nlen + elen
        raw = data[start:start + info.compress_size]
        blocks = None
        for b in (False, True):
            if lo_deflate(plain, b) == raw:
                blocks = b
                break
        if blocks is None:
            raise ValueError(f"{name}: compression of the fresh conversion not recognised")
        it = iter(values)
        new = OBJECT_ID.sub(lambda m: m.group(1) + next(it).encode("ascii") + m.group(3), plain)
        data = replace_part(data, name, new, lo_deflate(new, blocks))
        z = zipfile.ZipFile(io.BytesIO(data))
    return data


# ---------------------------------------------------------------- .docm route

VBA_PARTS = ("word/vbaproject.bin", "word/vbadata.xml", "word/_rels/vbaproject.bin.rels")
MACRO_MAIN = "application/vnd.ms-word.document.macroEnabled.main+xml"
PLAIN_MAIN = "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_DECL = re.compile(rb"^\s*<\?xml[^>]*\?>\s*")


def _xml_out(etree, original, root):
    decl = XML_DECL.match(original)
    return (decl.group(0) if decl else b"") + etree.tostring(root, encoding="UTF-8")


def docm_repackage(data):
    from lxml import etree
    parser = etree.XMLParser(resolve_entities=False)
    zin = zipfile.ZipFile(io.BytesIO(data))
    drop = {n for n in zin.namelist() if n.lower() in VBA_PARTS}
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            if info.filename in drop:
                continue
            part = zin.read(info.filename)
            low = info.filename.lower()
            if low == "[content_types].xml":
                root = etree.fromstring(part, parser)
                gone = {"/" + p.lower() for p in drop}
                for el in list(root):
                    if el.tag == f"{{{CT_NS}}}Override" and (el.get("PartName") or "").lower() in gone:
                        root.remove(el)
                    elif el.get("ContentType") == MACRO_MAIN:
                        el.set("ContentType", PLAIN_MAIN)
                part = _xml_out(etree, part, root)
            elif low.endswith(".rels"):
                root = etree.fromstring(part, parser)
                base = posixpath.dirname(posixpath.dirname(info.filename))
                gone = {p.lower() for p in drop}
                hit = []
                for el in root.iter(f"{{{REL_NS}}}Relationship"):
                    if el.get("TargetMode") == "External":
                        continue
                    target = unquote(el.get("Target") or "")
                    path = target.lstrip("/") if target.startswith("/") else \
                        posixpath.normpath(posixpath.join(base, target))
                    if path.lower() in gone:
                        hit.append(el)
                if hit:
                    for el in hit:
                        el.getparent().remove(el)
                    part = _xml_out(etree, part, root)
            zout.writestr(info, part)
    return out.getvalue()


# ---------------------------------------------------------------- driver

def safe_dest(dest, rel):
    norm = os.path.normpath(rel)
    if norm.startswith("..") or os.path.isabs(norm):
        raise ValueError(f"unsafe path {rel}")
    return os.path.join(dest, norm)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--dest", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--wg", nargs="*")
    ap.add_argument("--report")
    ap.add_argument("--convert-tmp", default=tempfile.gettempdir(),
                    help="shallow folder for the conversion trees (default: system temp)")
    a = ap.parse_args()
    rows = [json.loads(line) for line in open(a.manifest, encoding="utf-8")]
    if a.wg:
        rows = [r for r in rows if r["wg"] in a.wg]
    os.makedirs(a.work, exist_ok=True)
    os.makedirs(a.convert_tmp, exist_ok=True)
    cache, results = {}, []
    report = open(a.report, "w", encoding="utf-8") if a.report else None
    for i, r in enumerate(rows):
        t0 = time.time()
        res = {"path": r["path"], "wg": r["wg"], "kind": r["kind"], "url": r["url"],
               "archiveMatch": False, "memberMatch": None, "finalMatch": False, "error": None}
        blob, err, tried = None, None, []
        for url in [r["url"]] + list(r.get("urlAlternates") or []):
            if url in cache:
                blob, err = cache[url], None
                res["download"] = "reused"
            else:
                blob, err = fetch(url)
                time.sleep(PAUSE_SEC)
                for _ in range(2):  # a truncated body without a transport error shows as a hash mismatch
                    if blob is None or sha256(blob) == r["archiveSha256"]:
                        break
                    blob, err = fetch(url)
                    time.sleep(PAUSE_SEC)
                res["download"] = "ok" if blob is not None else "failed"
            tried.append({"url": url, "error": err,
                          "archiveMatch": blob is not None and sha256(blob) == r["archiveSha256"]})
            res["url"] = url
            if tried[-1]["archiveMatch"]:
                break
        if len(tried) > 1:
            res["tried"] = tried
        if blob is None:
            res["error"] = err
        else:
            res["archiveBytes"] = len(blob)
            res["archiveMatch"] = sha256(blob) == r["archiveSha256"]
            if res["archiveMatch"]:
                cache = {res["url"]: blob}
            data = blob
            try:
                if r.get("member"):
                    data = zipfile.ZipFile(io.BytesIO(blob)).read(r["member"])
                    res["memberMatch"] = sha256(data) == r["memberSha256"]
                conv = r.get("conversion")
                if conv and conv["method"] == "libreoffice":
                    wd = tempfile.mkdtemp(prefix=f"row{i:03d}-", dir=a.work)
                    name = r.get("member") or posixpath.basename(unquote(res["url"]))
                    out = libreoffice_convert(name, data, wd, conv["layout"], a.convert_tmp)
                    shutil.rmtree(wd, ignore_errors=True)
                    if out is None:
                        raise RuntimeError("LibreOffice produced no output")
                    if conv.get("objectIds"):
                        out = restore_object_ids(out, conv["objectIds"])
                    data = stamp_zip(out, conv["zipDateTime"][0])
                elif conv and conv["method"] == "docm-repackage":
                    data = docm_repackage(data)
                res["finalMatch"] = sha256(data) == r["sha256"]
                if res["finalMatch"]:
                    p = safe_dest(a.dest, r["path"])
                    os.makedirs(os.path.dirname(p), exist_ok=True)
                    with open(p, "wb") as f:
                        f.write(data)
            except (KeyError, zipfile.BadZipFile, RuntimeError, ValueError, OSError,
                    subprocess.TimeoutExpired) as e:
                res["error"] = f"{type(e).__name__}: {e}"
        res["seconds"] = round(time.time() - t0, 2)
        results.append(res)
        if report:
            report.write(json.dumps(res, ensure_ascii=False) + "\n")
            report.flush()
        print(f"[{i + 1}/{len(rows)}] {r['wg']} {r['kind']} archive={res['archiveMatch']} "
              f"member={res['memberMatch']} final={res['finalMatch']} {res['error'] or ''}",
              flush=True)
    summary = collections.defaultdict(collections.Counter)
    for res in results:
        for key in (res["wg"], res["kind"], "all"):
            summary[key]["rows"] += 1
            summary[key]["archiveMatch"] += res["archiveMatch"]
            summary[key]["memberMatch"] += bool(res["memberMatch"])
            summary[key]["finalMatch"] += res["finalMatch"]
    print(json.dumps({k: dict(v) for k, v in sorted(summary.items())}, indent=1))
    return 0 if all(res["finalMatch"] for res in results) else 1


if __name__ == "__main__":
    sys.exit(main())
