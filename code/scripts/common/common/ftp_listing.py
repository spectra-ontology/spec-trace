#!/usr/bin/env python3
"""ftp_listing.py — 공식 FTP 목록의 파일·폴더와 완전성을 검증한다.

Spec: docs/common/process/internal_deployment_readiness.md 작업 3.
Ontology: 회의 원문의 실제 폴더와 정본 회의 신원을 연결한다.
Cycle: 최초 수집, 원문 다운로드, 입력 승격.
배경: 3GPP의 폴더 href는 끝 / 가 없으며 없는 하위 경로도 403을 돌려준다.
사용: 회의 수집기와 bootstrap downloader가 import한다.
LLM 호출: 없음. HTTP 응답 원문을 검증하며 네트워크는 호출하지 않는다.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from urllib.parse import parse_qsl, unquote, urljoin, urlsplit

from bs4 import BeautifulSoup


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def local_file_name(name: str) -> str:
    """원격 이름을 한 번만 해석하고 %, DEL을 가역적인 로컬 문자로 보관한다.

    공식 목록에는 DEL이 포함된 ZIP이 있다. 그 이름을 삭제하거나 바꾸어 원격
    파일을 고르지 않고, 로컬의 % 자체도 escape해 literal %7F와 충돌을 막는다.
    """
    if (not name or name in {".", ".."} or "/" in name or "\\" in name
            or any(ord(c) < 32 for c in name)):
        raise ValueError("안전한 단일 원격 파일명이 아님")
    return name.replace("%", "%25").replace("\x7f", "%7F")


def remote_file_name(name: str) -> str:
    """local_file_name의 정규 출력만 역변환한다. 반복 unquote는 하지 않는다."""
    value = re.sub(r"%25|%7F", lambda m: "%" if m[0] == "%25" else "\x7f", name)
    if local_file_name(value) != name:
        raise ValueError("원격 파일명의 정규 로컬 표기가 아님")
    return value


def multiple_transport(url: str, name: str) -> dict:
    """공식 UI에 선언된 DEL ZIP 단일 선택 요청. 임의 HTTP 오류 fallback이 아니다."""
    parsed = urlsplit(url)
    parent, encoded = parsed.path.rsplit("/", 1)
    if (parsed.scheme != "https" or parsed.netloc != "www.3gpp.org"
            or parsed.query or parsed.fragment or not parent.endswith("/Docs")
            or "\x7f" not in name or not name.lower().endswith(".zip")
            or unquote(encoded, errors="strict") != name
            or any(ord(c) < 32 or ord(c) == 127 for c in url)):
        raise ValueError("공식 Docs의 광고된 DEL ZIP 요청이 아님")
    local_file_name(name)
    directory_url("https://www.3gpp.org" + parent)
    return {"method": "POST", "url": "https://www.3gpp.org" + parent + "?download=multiple",
            "selection": [name], "source_url": url, "remote_name": name,
            "local_name": local_file_name(name), "contract": "official-ui-download-multiple-v1"}


def meeting_folders(wg: str) -> list[str]:
    if wg not in {"RAN1", "RAN2", "RAN3", "RAN4", "RAN5"}:
        raise ValueError("명시적으로 지원하는 회의 WG가 아님")
    return ["Docs", "Report", "Reports"] if wg == "RAN4" else ["Docs", "Report"]


def directory_url(url: str) -> str:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != "www.3gpp.org"
            or parsed.query or parsed.fragment or not parsed.path.startswith("/ftp/")):
        raise ValueError("공식 HTTPS FTP 디렉터리 URL이 아님")
    parts = unquote(parsed.path, errors="strict").strip("/").split("/")
    if any(not p or p in {".", ".."} or "\\" in p or any(ord(c) < 32 or ord(c) == 127 for c in p)
           for p in parts):
        raise ValueError("디렉터리 URL에 안전하지 않은 경로 요소가 있음")
    return url.rstrip("/")


def parse_listing(html: bytes | str, url: str) -> list[dict]:
    """한 디렉터리의 전체 직접 자식을 읽는다. 불명확한 목록은 거절한다.

    제목의 경로, 단일 목록 table, 행별 icon/size, footer의 전체 항목 수가 모두
    일치해야 빈 하위 폴더를 증명할 수 있다. breadcrumb와 정렬 링크는 행이 아니다.
    """
    base = directory_url(url)
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    expected = unquote(urlsplit(base).path, errors="strict")
    if not title.startswith("Directory Listing ") or title[len("Directory Listing "):].rstrip("/") != expected:
        raise ValueError("FTP 목록 제목/요청 경로가 일치하지 않음")
    tables = soup.find_all("table")
    summaries = soup.find_all(string=re.compile(r"^\s*\d+ items\.\s*$"))
    if len(tables) != 1 or len(summaries) != 1 or summaries[0].find_parent("table"):
        raise ValueError("FTP 전체 목록 table/footer를 확인할 수 없음")
    bodies = tables[0].find_all("tbody", recursive=False)
    if len(bodies) != 1:
        raise ValueError("FTP 목록 tbody가 유일하지 않음")
    rows = bodies[0].find_all("tr", recursive=False)
    declared = int(str(summaries[0]).strip().split()[0])
    if len(rows) != declared:
        raise ValueError("FTP 전체 항목 수와 실제 목록 행 수가 다름")
    entries, seen = [], set()
    parent = unquote(urlsplit(base).path, errors="strict").rstrip("/")
    for row in rows:
        cells, links, icons = row.find_all("td", recursive=False), row.find_all("a", href=True), row.find_all("img")
        if len(cells) != 5 or len(links) != 1 or len(icons) != 1:
            raise ValueError("FTP 목록 행의 파일/폴더 구조가 불명확함")
        link = links[0]
        href = link["href"]
        # urljoin은 dot segment를 접으므로, 결합하기 전에 원래 href도 검사한다.
        raw_parts = unquote(urlsplit(href).path, errors="strict").split("/")
        if any(x in {".", ".."} for x in raw_parts) or re.search(r"%2f|%5c", href, re.I):
            raise ValueError("FTP 목록 링크에 dot/encoded separator가 있음")
        full = urljoin(base + "/", href)
        parsed = urlsplit(full)
        if (parsed.scheme != "https" or parsed.netloc != "www.3gpp.org"
                or parsed.query or parsed.fragment or parsed.username or parsed.password):
            raise ValueError("FTP 직접 자식 링크의 origin/query가 유효하지 않음")
        path = unquote(parsed.path, errors="strict").rstrip("/")
        name = path.rsplit("/", 1)[-1]
        if (path.rsplit("/", 1)[0] != parent or not name or name in {".", ".."}
                or "\\" in name or any(ord(c) < 32 for c in name)
                or link.get_text(" ", strip=True) != name or name in seen):
            raise ValueError("FTP 목록의 직접 자식 신원/이름이 유효하지 않음")
        icon = urlsplit(urljoin(base + "/", icons[0].get("src", "")))
        args = parse_qsl(icon.query, keep_blank_values=True)
        if icon.scheme != "https" or icon.netloc != "www.3gpp.org" or icon.path != "/ftp/geticon.axd" or len(args) != 1 or args[0][0] != "file":
            raise ValueError("FTP 파일/폴더 icon을 확인할 수 없음")
        size = cells[-1].get_text(" ", strip=True)
        kind = "directory" if args[0][1] == "" and not size else "file"
        if kind == "file" and (not re.fullmatch(r"\d+(?:[.,]\d+)?\s*(?:bytes?|[KMGT]?B)", size, re.I)
                               or full.endswith("/")):
            raise ValueError("FTP 파일 icon/크기/URL이 일치하지 않음")
        if kind == "directory" and "\x7f" in name:
            raise ValueError("제어문자 디렉터리를 거절함")
        entry = {"name": local_file_name(name) if kind == "file" else name,
                 "url": full, "kind": kind}
        if "\x7f" in name:
            selectors = row.find_all("input", {"type": "checkbox", "class": "downloadInput"})
            if len(selectors) != 1 or selectors[0].get("value") != name:
                raise ValueError("DEL 파일의 공식 선택 checkbox 신원이 다름")
            scripts = [script.get_text() for script in soup.find_all("script")]
            if not any(re.search(r'fetch\s*\(\s*location\.pathname\s*\+\s*[\'"]\?download=multiple[\'"]', script)
                       and re.search(r'method\s*:\s*[\'"]POST[\'"]', script)
                       and re.search(r'body\s*:\s*JSON\.stringify\(filesToDownload\)', script)
                       and "filesToDownload.push(filesInputs[i].value)" in script
                       for script in scripts):
                raise ValueError("DEL 원격 파일의 공식 선택 다운로드 계약이 없음")
            entry["source_transport"] = {**multiple_transport(full, name),
                                         "listing_page_sha256": digest(html.encode("utf-8") if isinstance(html, str) else html)}
        if entry["name"] != name:
            entry["source_name"] = name
        seen.add(name)
        entries.append(entry)
    return entries


def atomic_bytes(path: Path, body: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        raise ValueError("목록 출력 symlink를 거절함")
    handle, name = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def save_page(directory: Path, url: str, html: bytes | str, entries: list[dict]) -> dict:
    body = html.encode("utf-8") if isinstance(html, str) else html
    name = digest(body) + ".html.gz"
    target = directory / "listing-pages" / name
    compressed = gzip.compress(body, mtime=0)
    if target.exists():
        if target.is_symlink() or gzip.decompress(target.read_bytes()) != body:
            raise ValueError("기존 FTP 목록 원문이 바뀜")
    else:
        atomic_bytes(target, compressed)
    return {"url": url, "sha256": digest(body), "bytes": len(body),
            "raw_gzip": "listing-pages/" + name, "items": len(entries),
            "directories": [x["name"] for x in entries if x["kind"] == "directory"]}


def verify_inventory(directory: Path, meeting_list: Path, jobs: list[dict], selected: list[str],
                     source_relative: Path, base_url: str, folders: list[str], normalizer) -> dict:
    """다운로드 목록을 실제 전체 HTML closure와 대조하고 빈 정본 별칭만 분류한다.

    한 신원의 모든 폴더가 비었으면 계속 실패한다. 별칭은 같은 scope의 실자료
    폴더와 동일한 기존 canonicalMeetingNumber를 가져야 하며 원문 목록을 숨기지 않는다.
    """
    manifest_path = directory / "listing_manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("공식 회의 목록 완전성 검증 기록이 없음")
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_sha = digest(manifest_bytes)
    aria = directory / "urls_aria2.txt"
    if (manifest.get("schema") != 1 or manifest.get("meetings") != selected
            or manifest.get("meeting_list_sha256") != digest(meeting_list.read_bytes())
            or manifest.get("urls_sha256") != digest(aria.read_bytes())
            or manifest.get("folders") != folders or manifest.get("base_url") != base_url):
        raise ValueError("공식 목록 검증 기록의 범위/입력 SHA가 다름")
    records = manifest.get("pages", [])
    pages = {}
    for record in records:
        key = directory_url(record["url"])
        if key in pages:
            raise ValueError("중복 FTP 목록 검증 기록")
        relative = PurePosixPath(record["raw_gzip"])
        if relative.parts != ("listing-pages", record["sha256"] + ".html.gz"):
            raise ValueError("FTP 원문 검증 기록 경로가 유효하지 않음")
        path = directory / relative
        if path.is_symlink() or path.parent.is_symlink() or not path.is_file():
            raise ValueError("FTP 원문 검증 기록이 없거나 symlink임")
        body = gzip.decompress(path.read_bytes())
        if len(body) != record["bytes"] or digest(body) != record["sha256"]:
            raise ValueError("FTP 원문 검증 기록 SHA/크기가 다름")
        entries = parse_listing(body, record["url"])
        if len(entries) != record["items"] or [x["name"] for x in entries if x["kind"] == "directory"] != record["directories"]:
            raise ValueError("FTP 원문 분류와 검증 기록이 다름")
        pages[key] = entries
    visited, expected, absent, populated = set(), {}, [], set()
    special_downloads, name_mappings = {}, {}
    def walk(url, local, depth=0):
        key = directory_url(url)
        if depth > 5 or key in visited or key not in pages:
            raise ValueError("광고된 FTP 하위 목록이 누락/중복/깊이 초과임")
        visited.add(key)
        for entry in pages[key]:
            child = local / entry["name"]
            if entry["kind"] == "directory":
                walk(entry["url"], child, depth + 1)
            else:
                if entry["url"] in expected:
                    raise ValueError("중복 원문 URL")
                expected[entry["url"]] = child.as_posix()
                if "source_name" in entry:
                    name_mappings[child.as_posix()] = {"remote_name": entry["source_name"],
                                                       "local_name": entry["name"], "source_url": entry["url"]}
                if "source_transport" in entry:
                    special_downloads[child.as_posix()] = entry["source_transport"]
    for name in selected:
        key = directory_url(urljoin(base_url, name + "/"))
        if key not in pages:
            raise ValueError("선택 회의의 공식 상위 목록이 없음")
        visited.add(key)
        wanted = [x for x in pages[key] if x["name"] in folders]
        if any(x["kind"] != "directory" for x in wanted):
            raise ValueError("회의 자료 폴더가 파일로 광고됨")
        before = len(expected)
        for child in wanted:
            walk(child["url"], source_relative / name / child["name"])
        if len(expected) == before:
            absent.append(name)
        else:
            populated.add(name)
    if set(pages) != visited:
        raise ValueError("선택 수집 경로 밖 FTP 목록 검증 기록이 섞임")
    actual = {x["url"]: x["path"] for x in jobs}
    if len(actual) != len(jobs) or actual != expected:
        raise ValueError("원문 URL/로컬 경로가 공식 전체 파일 목록과 다름")
    aliases = {}
    for empty in absent:
        identity = normalizer(empty)
        counterparts = sorted(x for x in populated if identity and normalizer(x) == identity)
        if identity and not counterparts:
            raise ValueError("자료 폴더 없는 회의에 동일 정본 신원의 실제 자료가 없음: " + empty)
        if identity:
            aliases[empty] = {"canonical_meeting": identity, "represented_by": counterparts,
                              "root_page_sha256": next(x["sha256"] for x in records if directory_url(x["url"]) == directory_url(urljoin(base_url, empty + "/")))}
    if digest(manifest_path.read_bytes()) != manifest_sha:
        raise ValueError("검증 중 FTP 전체 목록 검증 기록이 바뀜")
    return {"manifest_sha256": manifest_sha, "placeholder_aliases": aliases,
            "official_file_count": len(expected), "verified_page_count": len(pages),
            "name_mappings": name_mappings, "special_downloads": special_downloads}
