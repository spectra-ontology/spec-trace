"""Python 3.10에서도 원래 예외에 보조 오류 설명을 덧붙입니다."""


def add_exception_note(error: BaseException, message: str) -> None:
    """원래 예외와 기존 메모를 유지하며 설명을 순서대로 추가합니다."""
    add_note = getattr(error, "add_note", None)
    if callable(add_note):
        add_note(message)
        return
    notes = getattr(error, "__notes__", None)
    if notes is None:
        error.__notes__ = [message]
    else:
        notes.append(message)
