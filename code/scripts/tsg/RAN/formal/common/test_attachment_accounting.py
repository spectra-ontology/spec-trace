"""합성 질의 결과로 공통 관계 적재 계측과 각 적재기의 연결을 확인한다.

LLM 호출·DB·네트워크 없음. 적재기의 DB 접근 경계는 합성 트랜잭션으로 대체한다.
"""
import contextlib
import importlib.util
import io
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from attachment_accounting import AttachAccounting

ROOT = next(p for p in Path(__file__).resolve().parents if (p / '.git').exists())


class AttachmentAccountingTests(unittest.TestCase):
    @staticmethod
    def transaction(attached):
        return SimpleNamespace(run=Mock(return_value=SimpleNamespace(single=lambda: {'n': attached})))

    def test_single_declarations_keep_missing_and_excess_separate(self):
        accounting = AttachAccounting()
        accounting.expect('REFERENCES', 'HAS_FIGURE')
        for count in (0, 3):
            tx = self.transaction(count)
            self.assertEqual(accounting.run(tx, 'REFERENCES', 'RETURN count(*) AS n', value='source'), count)
            tx.run.assert_called_once_with('RETURN count(*) AS n', value='source')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            accounting.report()
        self.assertIn('[REFERENCES] 선언 2건 → 부착 3행', output.getvalue())
        self.assertIn('짝 없음 1건 이상 · 여럿에 걸려 늘어난 행 2', output.getvalue())
        self.assertIn('[HAS_FIGURE] 선언 0건 → 부착 0행 (호출 0회', output.getvalue())

    def test_unwind_counts_batch_and_empty_batch(self):
        accounting = AttachAccounting()
        accounting.expect('MADE_AT')
        query = 'UNWIND $rows AS row RETURN count(*) AS n'
        accounting.run(self.transaction(2), 'MADE_AT', query, rows=[{}, {}, {}])
        accounting.run(self.transaction(0), 'MADE_AT', query, rows=[])
        self.assertEqual(accounting._rows['MADE_AT'], [3, 2, 1, 0])

    def test_unknown_relation_fails_before_query(self):
        accounting = AttachAccounting()
        accounting.expect('REFERENCES')
        tx = self.transaction(1)
        with self.assertRaises(KeyError):
            accounting.run(tx, 'REFERENCE', 'RETURN count(*) AS n')
        tx.run.assert_not_called()

    def test_all_seven_loaders_share_code_with_independent_accounting(self):
        paths = [ROOT / f'scripts/tsg/RAN/formal/RAN{wg}/phase-2/neo4j/01_load_decisions.py'
                 for wg in range(1, 6)]
        paths.extend(ROOT / f'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/0{number}_load_{name}.py'
                     for number, name in ((2, 'roles'), (3, 'embedded')))
        instances = []
        for index, path in enumerate(paths):
            spec = importlib.util.spec_from_file_location(f'_attachment_loader_{index}', path)
            module = importlib.util.module_from_spec(spec)
            with patch.dict(os.environ, {'NEO4J_PASSWORD': 'isolated-fixture-no-database'}):
                spec.loader.exec_module(module)
            self.assertIs(type(module.ATTACHMENTS), AttachAccounting)
            self.assertTrue(module.ATTACHMENTS._expected)
            instances.append(module.ATTACHMENTS)
        instances[0]._rows['synthetic'] = [1, 1, 0, 0]
        self.assertTrue(all(not instance._rows for instance in instances[1:]))

    def test_embedded_main_uses_new_run_for_replaced_relationship_targets(self):
        path = ROOT / 'scripts/tsg/RAN/formal/RAN1/phase-2/neo4j/03_load_embedded.py'
        spec = importlib.util.spec_from_file_location('_embedded_run_identity_fixture', path)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(os.environ, {'NEO4J_PASSWORD': 'isolated-fixture-no-database'}):
            spec.loader.exec_module(module)

        class QueryResult:
            def single(self):
                return {'fig_cnt': 1, 'tbl_cnt': 0, 'cht_cnt': 0, 'n': 1, 'c': 0}

            def __iter__(self):
                return iter(())

        query = Mock(return_value=QueryResult())
        tx = SimpleNamespace(run=query, commit=Mock())
        session = SimpleNamespace(
            run=query, execute_write=lambda function: function(tx),
            begin_transaction=lambda: contextlib.nullcontext(tx))
        driver = SimpleNamespace(session=lambda: contextlib.nullcontext(session), close=Mock())
        graph = SimpleNamespace(driver=Mock(return_value=driver))

        def inputs(figure_id):
            return {
                'figures.jsonld': [{'figureId': figure_id}],
                'tables.jsonld': [], 'charts.jsonld': [],
                'resolutions_agreements.jsonld': [
                    {'resolutionId': 'synthetic-resolution', 'hasFigure': ['tdoc:figure/' + figure_id]}],
                'resolutions_conclusions.jsonld': [],
                'resolutions_working_assumptions.jsonld': [],
            }

        relationships = []
        cleanup_runs = []
        with patch.object(module, 'GraphDatabase', graph), \
             patch.object(module, '_accept_inputs', side_effect=[inputs('previous'), inputs('current')]), \
             contextlib.redirect_stdout(io.StringIO()):
            for _ in range(2):
                start = query.call_count
                stats = module.main()
                self.assertEqual(stats['figures'], 1)
                calls = query.call_args_list[start:]
                created = [(call.kwargs['figId'], call.kwargs['run']) for call in calls
                           if 'MERGE (res)-[e:HAS_FIGURE]' in call.args[0]]
                self.assertEqual(len(created), 1)
                relationships.append(created[0])
                cleanup = [call for call in calls if "WHERE coalesce(r._run, '') <> $run" in call.args[0]]
                self.assertEqual(len(cleanup), len(module.OWNED_EDGES))
                self.assertEqual({call.kwargs['run'] for call in cleanup}, {created[0][1]})
                cleanup_runs.append(cleanup[0].kwargs['run'])

        self.assertEqual([target for target, _ in relationships], ['previous', 'current'])
        # 이전 관계의 RUN이 현재 정리 조건과 달라야 삭제 대상에 포함된다.
        self.assertNotEqual(relationships[0][1], cleanup_runs[1])
        driver.close.assert_called_with()
        self.assertEqual(driver.close.call_count, 2)
        self.assertEqual(tx.commit.call_count, 2)


if __name__ == '__main__':
    unittest.main()
