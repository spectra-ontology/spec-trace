"""구조 메타데이터와 구분하여 payload의 문자열 본문을 선택합니다."""

from collections.abc import Mapping, Sequence


def first_text_field(payload: Mapping, fields: Sequence[str] = ("text", "content", "asn1")) -> str:
    """우선순위에 따라 첫 비어 있지 않은 문자열을 반환합니다.

    구조 객체·목록·숫자는 본문으로 변환하지 않습니다. 문자열의 공백과 줄바꿈은
    보존하며, 본문 후보가 없으면 빈 문자열을 반환합니다.
    """
    if not isinstance(payload, Mapping):
        raise ValueError("Qdrant payload는 필드 이름을 가진 객체여야 합니다")
    return next((payload[field] for field in fields
                 if isinstance(payload.get(field), str) and payload[field]), "")
