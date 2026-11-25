"""ETSI 메시지 목록의 구조와 WG 신원을 검사하는 공용 파서.

Spec: docs/tsg/RAN/email/email_layer_plan.md의 이메일 E-0 수집 경로.
현행 수집기와 독립 corpus 수집기가 같은 HTML 판정을 사용합니다.
HTTP 요청이나 파일 쓰기는 수행하지 않습니다. 저장 index의 신원과 수집 완료 기록을 대조합니다.
"""
from datetime import datetime
import re
import json
import hashlib
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

NR_START_ARCHIVES = {
    "RAN1": "1604A", "RAN2": "1605A", "RAN3": "1606A",
    "RAN4": "1612A", "RAN5": "1709A", "TSG_RAN": "1603A",
}


def archive_code_year_month(code: str):
    """YYMM[A-E][_N]의 날짜. 메시지 정렬기와 같은 50년 세기 경계를 씁니다."""
    if not isinstance(code, str) or not re.fullmatch(r'\d{4}[A-E](?:_\d+)?', code):
        return None
    year, month = int(code[:2]), int(code[2:4])
    if not 1 <= month <= 12:
        return None
    return (2000 + year if year <= 50 else 1900 + year), month


def load_archive_records(path: Path, *, require_url=False):
    """빈·손상·중복 inventory를 후속 수집 전에 거절합니다."""
    records, seen = [], set()
    with open(path, encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise ValueError(f'{path}:{line_number}: archive JSON 형식을 확인하세요') from exc
            code = record.get('archive_code') if isinstance(record, dict) else None
            if archive_code_year_month(code) is None or code in seen:
                raise ValueError(f'{path}:{line_number}: archive_code 형식·중복을 확인하세요')
            if require_url and (not isinstance(record.get('url'), str) or not record['url'].strip()):
                raise ValueError(f'{path}:{line_number}: archive URL을 확인하세요')
            seen.add(code)
            records.append(record)
    if not records:
        raise ValueError(f'{path}: archive 목록이 비어 있습니다')
    return records


def index_identities(path):
    """수집 완료 기록과 대조할 저장 신원. 손상·중복 행은 보존 후 거절합니다."""
    path = Path(path)
    identities = {}
    if not path.exists():
        return identities
    with path.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except ValueError as exc:
                raise ValueError(f'{path}:{number}: 메시지 JSON을 확인하세요') from exc
            code = record.get('archive_code') if isinstance(record, dict) else None
            msg_id = record.get('msg_id') if isinstance(record, dict) else None
            if (not archive_code_to_sortkey(code) or code != code.upper()
                    or not isinstance(msg_id, str) or not msg_id.strip()):
                raise ValueError(f'{path}:{number}: 메시지 신원을 확인하세요')
            ids = identities.setdefault(code, set())
            if msg_id in ids:
                raise ValueError(f'{path}:{number}: 중복 메시지 신원을 확인하세요')
            ids.add(msg_id)
    return identities


def archive_receipt(url, identities):
    """다른 archive의 append와 독립적인 다운로드 URL·신원 집합의 완료 증거."""
    content = json.dumps(sorted(identities), ensure_ascii=False).encode('utf-8')
    return {'source_url': url, 'messages': len(identities),
            'msg_ids_sha256': hashlib.sha256(content).hexdigest()}


def archive_code_to_sortkey(code):
    """연도·월·주차 순서의 정렬 키. A=0이며 잘못된 코드는 0입니다."""
    match = re.fullmatch(r"(\d{2})(0[1-9]|1[0-2])([A-E])(?:_\d+)?", code.upper()) if isinstance(code, str) else None
    if match is None:
        return 0
    year, month = archive_code_year_month(code.upper())
    week = match.group(3)
    return year * 10000 + month * 100 + ord(week) - ord("A")


def parse_message_index(html, *, list_name, wg, archive_code, archive_url):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", id=f"{list_name}-a1-table")
    identified = bool(tables)
    if not tables:
        tables = soup.find_all("table", class_="width-100")
    if len(tables) != 1:
        raise ValueError("선택한 메일링 리스트의 메시지 목록 표를 확인할 수 없습니다")

    messages, seen = [], set()
    for row in tables[0].find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        link = cells[0].find("a", href=True)
        if link is None:
            continue
        detail_url = urljoin(archive_url, link["href"])
        parsed = urlsplit(detail_url)
        params = parse_qs(parsed.query, keep_blank_values=True, errors="strict")
        keys = [key for key in params if key.upper() == "A2"]
        if not keys:
            continue
        if (len(cells) < 3 or parsed.scheme != "https" or parsed.netloc != "list.etsi.org"
                or parsed.fragment or len(keys) != 1 or len(params[keys[0]]) != 1):
            raise ValueError("메시지 행의 형식 또는 ETSI 링크가 유효하지 않습니다")
        identity = params[keys[0]][0].split(";", 1)
        if len(identity) != 2 or identity[0].upper() != list_name.upper():
            raise ValueError("메시지 링크의 메일링 리스트가 선택한 WG와 다릅니다")
        msg_id = identity[1]
        if not msg_id or any(ord(char) < 32 or ord(char) == 127 or char in "/\\" for char in msg_id):
            raise ValueError("메시지 식별자가 유효하지 않습니다")
        if msg_id in seen:
            raise ValueError("목록에 중복 메시지 식별자가 있습니다")
        seen.add(msg_id)
        messages.append({
            "wg": wg, "archive_code": archive_code, "msg_id": msg_id,
            "subject": link.get_text(strip=True),
            "sender_raw": cells[1].get_text(strip=True),
            "date_str": cells[2].get_text(strip=True),
            "detail_url": detail_url, "crawled_at": datetime.now().isoformat(),
        })
    if not identified and not messages:
        raise ValueError("일반 표만 있는 응답에서 빈 메시지 목록을 확인할 수 없습니다")
    return messages
