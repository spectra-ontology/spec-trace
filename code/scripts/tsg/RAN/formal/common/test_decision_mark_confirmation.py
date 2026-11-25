"""Synthetic working-assumption confirmation grammar regressions."""

import unittest

from decision_marks import classify, decision_spans


class ConfirmationGrammar(unittest.TestCase):
    def test_negated_or_conditional_confirmation_remains_working_assumption(self):
        for qualifier in (
            'not confirmed as agreement',
            'not yet confirmed as agreement',
            'never formally confirmed as agreement',
            'confirmed as agreement if the condition holds',
            'confirmed as agreement unless the condition changes',
        ):
            with self.subTest(qualifier=qualifier):
                mark = classify(f'Working assumption ({qualifier}):')
                self.assertIsNotNone(mark)
                self.assertEqual(mark.kind, 'working_assumption')
        for text in (
            'Working assumption is confirmed as agreement if the condition holds:',
            'Working assumption is confirmed as agreement unless the condition changes:',
            'Working assumption is confirmed if the condition holds:',
        ):
            with self.subTest(text=text):
                self.assertEqual(classify(text).kind, 'working_assumption')

    def test_explicit_unconditional_confirmations_still_promote(self):
        for text in (
            'Working assumption (confirmed as agreement):',
            'Working assumption (confirmed as a formal agreement):',
            'Working assumptions are confirmed:',
            'Working assumption is confirmed as agreement:',
        ):
            with self.subTest(text=text):
                self.assertEqual(classify(text).kind, 'agreement')

    def test_condition_before_confirmation_preserves_working_assumption(self):
        for text in (
            'Working assumption for the case if the proposal is confirmed as agreement:',
            'Working assumption for the case unless the proposal is confirmed as agreement:',
            'Working assumption (if the proposal is confirmed as agreement):',
            'Working assumption (unless the proposal is confirmed as agreement):',
            'Working assumption (if the condition holds, confirmed as agreement):',
            'Working assumption (unless the condition changes, confirmed as agreement):',
        ):
            with self.subTest(text=text):
                mark = classify(text)
                self.assertIsNotNone(mark)
                self.assertEqual(mark.kind, 'working_assumption')
                texts = [text, 'Synthetic body', '']
                marks = list(decision_spans(texts, [False, False, True], [False] * 3, []))
                self.assertEqual(len(marks), 1)
                self.assertEqual(marks[0][1].kind, 'working_assumption')

    def test_separate_prior_clause_condition_does_not_qualify_confirmation(self):
        for text in (
            'Working assumption (if required, discuss the draft separately) is confirmed as agreement:',
            'Working assumption (unless required, omit the separate review) is confirmed as agreement:',
            'Working assumption (if required, discuss the draft separately). Confirmed as agreement:',
            'Working assumption (unless required, omit the separate review). Confirmed as agreement:',
            'Working assumption for a case if a later review is needed. Confirmed as agreement:',
            'Working assumption for a case unless a later review is needed. Confirmed as agreement:',
        ):
            with self.subTest(text=text):
                mark = classify(text)
                self.assertIsNotNone(mark)
                self.assertEqual(mark.kind, 'agreement')

    def test_original_kind_filter_and_explicit_following_agreement_are_preserved(self):
        self.assertEqual(classify('Working assumption (confirmed as agreement):',
                                 ('working_assumption',)).kind, 'working_assumption')
        self.assertEqual(classify('Working assumption (confirmed as agreement below):').kind,
                         'working_assumption')
        texts = ['Working assumption (not confirmed as agreement):', 'Synthetic body', '']
        marks = list(decision_spans(texts, [False, False, True], [False] * 3, []))
        self.assertEqual(len(marks), 1)
        self.assertEqual(marks[0][1].kind, 'working_assumption')


if __name__ == '__main__':
    unittest.main()
