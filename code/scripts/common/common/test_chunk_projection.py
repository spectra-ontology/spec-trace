"""Synthetic generation admission tests; no model, network, or database."""
import unittest

from scripts.common.common.chunk_projection import require_chunk_projection


class ChunkProjection(unittest.TestCase):
    def check_projection(self, chunks, **kwargs):
        return require_chunk_projection(chunks, owner_key='specNumber', owner='38.001',
                                        point_id=kwargs.pop('point_id', lambda cid: cid), **kwargs)

    def test_complete_generation_is_returned_without_filtering(self):
        chunks = [dict(text='Body', chunkId='a', specNumber='38.001'),
                  dict(text='Second body', chunkId='b', specNumber='38.001')]
        self.assertIs(self.check_projection(chunks), chunks)

    def test_rejects_malformed_member_and_identity_collisions(self):
        good = dict(text='Body', chunkId='a', specNumber='38.001')
        for chunks in (None, {}, [], [None], [dict(good, text=None)],
                       [dict(good, text=' ')], [dict(good, text=3)],
                       [dict(good, chunkId=None)], [dict(good, chunkId=' ')],
                       [dict(good, specNumber='other')], [good, dict(good)],
                       [good, dict(good, chunkId='b', text='')]):
            with self.subTest(chunks=chunks), self.assertRaises(ValueError):
                self.check_projection(chunks)
        with self.assertRaisesRegex(ValueError, 'point ID collision'):
            self.check_projection([good, dict(good, chunkId='b')], point_id=lambda cid: 1)

    def test_content_fallback_matches_ran5_embedding_input(self):
        chunks = [dict(text='', content='Body', chunkId='a', specNumber='38.001')]
        self.assertIs(self.check_projection(chunks, text_keys=('text', 'content')), chunks)


if __name__ == '__main__':
    unittest.main()
