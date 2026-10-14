import unittest
from analyze_predictions import gated, paired

class AnalysisTests(unittest.TestCase):
    def test_failure_on_empty_gold_never_scores_correct(self):
        raw={'exact':True,'f1':1.,'precision':1.,'recall':1.,'matched_records':0,'gold_records':0,'predicted_records':0}
        result=gated(raw,'GENERATION_ERROR')
        self.assertFalse(result['exact']);self.assertEqual(result['f1'],0)
        self.assertTrue(result['raw_scorer_exact'])
    def test_actual_empty_success_retains_correct(self):
        raw={'exact':True,'f1':1.,'matched_records':0}
        self.assertTrue(gated(raw,'OK')['exact'])
    def test_partial_records_retain_matching_credit(self):
        raw={'exact':False,'f1':.5,'matched_records':1,'gold_records':3}
        self.assertEqual(gated(raw,'PARTIAL')['f1'],.5)
    def test_incomplete_empty_answer_does_not_establish_empty_gold(self):
        raw={'exact':True,'f1':1.,'matched_records':0,'gold_records':0}
        self.assertFalse(gated(raw,'PARTIAL')['exact'])
    def test_paired_uses_same_ids(self):
        with self.assertRaises(ValueError):paired({'a':{'f1':1}},{'b':{'f1':0}},'f1')
    def test_paired_zero_difference_is_zero(self):
        a={'a':{'f1':1},'b':{'f1':0}}
        r=paired(a,a,'f1',replicates=100)
        self.assertEqual(r['paired_bootstrap_95_percentile_ci'],[0,0])

if __name__=='__main__':unittest.main()
