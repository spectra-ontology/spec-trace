"""원래 예외와 보조 오류 메모의 Python 3.10 호환성을 검사합니다."""

import unittest

from exception_notes import add_exception_note


class LegacyError(Exception):
    add_note = None


class NativeError(Exception):
    def add_note(self, message):
        self.calls.append(message)
        self.__notes__.append(message)


class ExceptionNotesTests(unittest.TestCase):
    def test_callable_native_method_receives_each_note(self):
        error = NativeError("primary")
        error.calls = []
        notes = error.__notes__ = ["original context"]
        add_exception_note(error, "secondary failure")
        self.assertEqual(error.calls, ["secondary failure"])
        self.assertIs(error.__notes__, notes)
        self.assertEqual(notes, ["original context", "secondary failure"])

    def test_legacy_exception_creates_notes_and_appends_in_order(self):
        error = LegacyError("primary")
        add_exception_note(error, "first failure")
        notes = error.__notes__
        add_exception_note(error, "second failure")
        self.assertIs(error.__notes__, notes)
        self.assertEqual(notes, ["first failure", "second failure"])

    def test_legacy_exception_preserves_an_existing_empty_or_nonempty_list(self):
        for initial in ([], ["original context"]):
            with self.subTest(initial=initial):
                error = LegacyError("primary")
                notes = error.__notes__ = list(initial)
                add_exception_note(error, "secondary failure")
                self.assertIs(error.__notes__, notes)
                self.assertEqual(notes, initial + ["secondary failure"])

    def test_cleanup_note_preserves_original_exception_identity_and_type(self):
        for error_type in (ValueError, KeyboardInterrupt, SystemExit, LegacyError):
            with self.subTest(error_type=error_type):
                error = error_type("primary")
                error.__notes__ = ["original context"]
                with self.assertRaises(error_type) as caught:
                    try:
                        raise error
                    finally:
                        try:
                            raise OSError("close failed")
                        except OSError as close_error:
                            add_exception_note(error, f"secondary: {close_error}")
                self.assertIs(caught.exception, error)
                self.assertIs(type(caught.exception), error_type)
                self.assertEqual(error.__notes__, ["original context", "secondary: close failed"])


if __name__ == "__main__":
    unittest.main()
