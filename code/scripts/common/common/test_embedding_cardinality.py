"""Local token accounting and vectorization preserve declared input contracts."""
from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

import embedding_registry as registry


class EmbeddingCardinalityTests(unittest.TestCase):
    def test_implicit_model_prompt_is_rejected_before_token_accounting(self):
        encoder = registry.Encoder("prompted", "local", "fixture/model", 3, 10, "a" * 40)
        model = SimpleNamespace(default_prompt_name="query", prompts={"query": "query prefix"},
                                max_seq_length=10, get_embedding_dimension=lambda: 3)
        module = SimpleNamespace(SentenceTransformer=lambda *args, **kwargs: model)
        with patch.dict(sys.modules, sentence_transformers=module), \
                patch.object(registry, "local_snapshot_path", return_value="synthetic-snapshot"), \
                patch.dict(registry._LOCAL_CACHE, clear=True), \
                self.assertRaisesRegex(ValueError, "implicit default prompt"):
            registry.load_local_encoder(encoder, device="cpu")
        self.assertNotIn("prompted", registry._LOCAL_CACHE)

    def test_short_tokenizer_output_fails(self):
        enc = SimpleNamespace(key='fixture', max_tokens=10)
        tok = Mock(return_value={'input_ids': [[1]]})
        tok.num_special_tokens_to_add.return_value = 2
        with patch.object(registry, 'load_local_encoder', return_value=SimpleNamespace(tokenizer=tok)):
            with self.assertRaisesRegex(ValueError, 'tokenizer returned 1 rows for 2 texts'):
                registry.truncate_to_encoder_budget(enc, ['a','b'])

    def test_short_vector_output_fails_and_complete_output_passes(self):
        enc = SimpleNamespace(key='fixture', max_tokens=10)
        vector = Mock()
        vector.tolist.return_value = [0.5]
        model = Mock()
        model.encode.return_value = [vector]
        with patch.object(registry, 'truncate_to_encoder_budget', return_value=(['a','b'],0)), \
                patch.object(registry, 'load_local_encoder', return_value=model):
            with self.assertRaisesRegex(ValueError, 'encoder returned 1 vectors for 2 texts'):
                registry.embed_local(enc, ['a','b'])
            model.encode.return_value = [vector, vector]
            self.assertEqual(registry.embed_local(enc, ['a','b']), [[0.5],[0.5]])

    def test_empty_input_never_loads_encoder(self):
        with patch.object(registry, 'load_local_encoder') as loader:
            self.assertEqual(registry.embed_local(SimpleNamespace(key='fixture'), []), [])
            loader.assert_not_called()

    def test_budget_must_leave_room_for_body_tokens(self):
        tok = Mock()
        tok.num_special_tokens_to_add.return_value = 2
        with patch.object(registry, 'load_local_encoder', return_value=SimpleNamespace(tokenizer=tok)):
            for budget in (1, 2):
                with self.subTest(budget=budget), self.assertRaisesRegex(ValueError, 'no room'):
                    registry.truncate_to_encoder_budget(SimpleNamespace(key='fixture', max_tokens=budget), ['body'])
        tok.assert_not_called()

    def test_decoded_prefix_is_recounted_before_return(self):
        class Tokenizer:
            def num_special_tokens_to_add(self):
                return 2

            def __call__(self, texts, **kwargs):
                if isinstance(texts, list):
                    return {'input_ids': [list(range(len(text))) for text in texts]}
                return {'input_ids': list(range(len(texts)))}

            def decode(self, tokens, **kwargs):
                # A decoded prefix can occupy more tokens when encoded again.
                return 'x' * (len(tokens) + 1)

        tok = Tokenizer()
        enc = SimpleNamespace(key='fixture', max_tokens=5)
        with patch.object(registry, 'load_local_encoder', return_value=SimpleNamespace(tokenizer=tok)):
            texts, cut = registry.truncate_to_encoder_budget(enc, ['abcdefgh', 'ok'])
        self.assertEqual(texts, ['xxx', 'ok'])
        self.assertEqual(cut, 1)
        self.assertLessEqual(len(tok(texts[0])['input_ids']) + 2, enc.max_tokens)

    def test_unrepresentable_decoded_prefix_fails_without_looping(self):
        tok = Mock(side_effect=lambda text, **kw: {'input_ids': [[1, 2, 3, 4]]}
                   if isinstance(text, list) else {'input_ids': [1, 2, 3, 4]})
        tok.num_special_tokens_to_add.return_value = 2
        tok.decode.return_value = 'always too large'
        with patch.object(registry, 'load_local_encoder', return_value=SimpleNamespace(tokenizer=tok)), \
                self.assertRaisesRegex(ValueError, 'cannot fit'):
            registry.truncate_to_encoder_budget(SimpleNamespace(key='fixture', max_tokens=5), ['body'])
        self.assertEqual(tok.decode.call_count, 4)


if __name__ == '__main__':
    unittest.main()
