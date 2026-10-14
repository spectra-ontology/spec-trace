import copy
import unittest
import scorer


def contract(kind='set', fields=None, cardinality=None):
    return {'validation_status':'validated',
            'required_fields':fields or [{'name':'status','type':'string'}, {'name':'count','type':'integer'}],
            'collection':{'kind':kind}, 'cardinality_policy':cardinality or {'mode':'all'}}


class ContractScoringTests(unittest.TestCase):
    def test_distribution_requires_the_correct_count(self):
        c=contract(); gold=[{'status':'approved','count':7}]
        self.assertTrue(scorer.score(c,gold,gold)['exact'])
        self.assertFalse(scorer.score(c,gold,[{'status':'approved','count':8}])['exact'])
        self.assertFalse(scorer.score(c,gold,[{'status':'approved'}])['exact'])

    def test_roles_are_named(self):
        c=contract(fields=[{'name':'sender','type':'string'},{'name':'recipient','type':'string'}])
        gold=[{'sender':'RAN1','recipient':'RAN2'}]
        self.assertFalse(scorer.score(c,gold,[{'sender':'RAN2','recipient':'RAN1'}])['exact'])

    def test_numeric_string_and_boolean_do_not_match_integer(self):
        c=contract();gold=[{'status':'approved','count':2}]
        for wrong in ['2',True,2.0,None]:
            self.assertFalse(scorer.score(c,gold,[{'status':'approved','count':wrong}])['exact'])

    def test_invalid_records_do_not_collapse_by_error_type(self):
        c=contract(fields=[{'name':'n','type':'integer'}])
        result=scorer.score(c,[{'n':2}],[{'n':2},{'n':'2'},{'n':'bad'}])
        self.assertEqual(result['predicted_records'],3)
        self.assertAlmostEqual(result['precision'],1/3)

    def test_null_is_different_from_a_missing_field(self):
        c=contract(fields=[{'name':'status','type':'string','nullable':True}])
        self.assertTrue(scorer.score(c,[{'status':None}],[{'status':None}])['exact'])
        self.assertFalse(scorer.score(c,[{'status':None}],[{}])['exact'])

    def test_optional_context_columns_are_not_silently_graded(self):
        c=contract();gold=[{'status':'approved','count':7,'context':'source'}]
        pred=[{'status':'approved','count':7,'context':'different'}]
        self.assertTrue(scorer.score(c,gold,pred)['exact'])

    def test_missing_and_extra_required_records(self):
        c=contract();gold=[{'status':'approved','count':7},{'status':'noted','count':2}]
        self.assertFalse(scorer.score(c,gold,gold[:1])['exact'])
        self.assertFalse(scorer.score(c,gold,gold+[{'status':'other','count':1}])['exact'])

    def test_set_and_multiset_have_different_duplicate_semantics(self):
        row={'status':'approved','count':7}
        self.assertTrue(scorer.score(contract('set'),[row],[row,row])['exact'])
        self.assertFalse(scorer.score(contract('multiset'),[row],[row,row])['exact'])

    def test_sequence_scores_positions(self):
        gold=[{'status':'approved','count':7},{'status':'noted','count':2}]
        c=contract('sequence')
        c['collection']['order_keys']=[{'field':'count','direction':'desc'}]
        self.assertFalse(scorer.score(c,gold,list(reversed(gold)))['exact'])
        with self.assertRaises(ValueError):
            scorer.score(c,list(reversed(gold)),list(reversed(gold)))

    def test_order_definition_must_use_valid_named_keys(self):
        c=contract('sequence');gold=[{'status':'approved','count':7}]
        for keys in [[],[{'field':'absent','direction':'asc'}],[{'field':'count','direction':'invalid'}]]:
            c['collection']['order_keys']=keys
            with self.assertRaises(ValueError):scorer.score(c,gold,gold)

    def test_ordered_ties_allow_only_equal_key_permutations(self):
        c=contract('ordered_ties')
        c['collection'].update(order_keys=[{'field':'count','direction':'desc'}],tie_policy='any_order_within_equal_keys')
        gold=[{'status':'a','count':7},{'status':'b','count':7},{'status':'c','count':2}]
        self.assertTrue(scorer.score(c,gold,[gold[1],gold[0],gold[2]])['exact'])
        self.assertFalse(scorer.score(c,gold,list(reversed(gold)))['exact'])

    def test_declared_exact_cardinality(self):
        row={'status':'approved','count':7}
        c=contract('multiset',cardinality={'mode':'exact','value':1})
        self.assertFalse(scorer.score(c,[row],[row,row])['exact'])
        with self.assertRaises(ValueError):scorer.score(c,[row,row],[row])

    def test_nested_structure_and_collection_semantics(self):
        fields=[{'name':'impact','type':'json','json_schema':{'type':'array','items':{'type':'object','properties':{'spec':{'type':'string'},'count':{'type':'integer'}},'required':['spec','count'],'additionalProperties':False}},'nested_array_semantics':{'$':'set'}}]
        c=contract(fields=fields);gold=[{'impact':[{'spec':'38.211','count':3},{'spec':'38.212','count':1}]}]
        pred=[{'impact':list(reversed(gold[0]['impact']))}]
        self.assertTrue(scorer.score(c,gold,pred)['exact'])
        wrong=[{'impact':[{'spec':'38.211','count':'3'},{'spec':'38.212','count':1}]}]
        self.assertFalse(scorer.score(c,gold,wrong)['exact'])
        c['required_fields'][0]['nested_array_semantics']['$']='sequence'
        self.assertFalse(scorer.score(c,gold,pred)['exact'])

    def test_unvalidated_tasks_have_no_benchmark_score(self):
        c=contract();c['validation_status']='pending';row={'status':'approved','count':7}
        with self.assertRaises(ValueError):scorer.score(c,[row],[row])
        self.assertTrue(scorer.score(c,[row],[row],diagnostic=True)['diagnostic_only'])

    def test_empty_result_is_formal_empty_not_abstention(self):
        self.assertTrue(scorer.score(contract(),[],[])['exact'])
        self.assertFalse(scorer.score(contract(),[],[{'status':'approved','count':0}])['exact'])

    def test_more_than_historical_2000_records(self):
        c=contract(fields=[{'name':'n','type':'integer'}]);rows=[{'n':i} for i in range(2500)]
        self.assertTrue(scorer.score(c,rows,rows)['exact'])

    def test_exact_json_rejects_duplicate_keys_and_nonfinite(self):
        mod=scorer.get_kernel()
        for value in ['{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}']:
            with self.assertRaises(ValueError):mod.loads_exact(value)

    def test_number_preserves_decimal_value(self):
        mod=scorer.get_kernel();c=contract(fields=[{'name':'rate','type':'number'}])
        self.assertTrue(scorer.score(c,mod.loads_exact('[{"rate":9.3}]'),mod.loads_exact('[{"rate":9.30}]'))['exact'])
        self.assertFalse(scorer.score(c,mod.loads_exact('[{"rate":9.3}]'),mod.loads_exact('[{"rate":9.3000001}]'))['exact'])


if __name__=='__main__':unittest.main()
