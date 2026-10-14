"""Offline tests for ranked retrieval metrics and hybrid fusion."""

import unittest
from core.retrieval import HybridRetriever, reciprocal_rank_fusion
from core.retrieval_eval import retrieval_metrics
from core.catalog import catalog_document, get_catalog


class RetrievalEvaluationTests(unittest.TestCase):
    def test_rrf_combines_rankings_deterministically(self):
        fused = reciprocal_rank_fusion(
            (["doc-a", "doc-b"], ["doc-b", "doc-c"]),
            k=60,
        )
        self.assertEqual(fused[0][0], "doc-b")
        self.assertGreater(fused[0][1], fused[1][1])
        self.assertEqual(fused, reciprocal_rank_fusion((["doc-a", "doc-b"], ["doc-b", "doc-c"]), k=60))

    def test_recall_precision_and_mrr_for_expected_product_ids(self):
        metrics = retrieval_metrics(["KLS-001", "DTK-005", "NVY-003"], ["KLS-001", "NVY-003"], 3)
        self.assertEqual(metrics["recall@3"], 1.0)
        self.assertAlmostEqual(metrics["precision@3"], 2 / 3)
        self.assertEqual(metrics["mrr"], 1.0)

    def test_no_relevant_result_scores_zero(self):
        metrics = retrieval_metrics(["DTK-005", "KSH-004"], ["SLK-006"], 2)
        self.assertEqual(metrics["recall@2"], 0.0)
        self.assertEqual(metrics["precision@2"], 0.0)
        self.assertEqual(metrics["mrr"], 0.0)

    def test_duplicate_chunks_for_one_product_count_once(self):
        metrics = retrieval_metrics(["KLS-001", "KLS-001", "KLS-001", "DTK-005"], ["KLS-001"], 2)
        self.assertEqual(metrics["recall@2"], 1.0)
        self.assertEqual(metrics["precision@2"], 0.5)

    def test_metrics_reject_invalid_cutoff_or_empty_ground_truth(self):
        with self.assertRaises(ValueError):
            retrieval_metrics(["KLS-001"], ["KLS-001"], 0)
        with self.assertRaises(ValueError):
            retrieval_metrics(["KLS-001"], [], 2)

    def test_product_code_is_extracted_from_chunk(self):
        self.assertEqual(
            HybridRetriever._product_code("Tuotekoodi: KLS-001\nKuvaus: merinovilla"),
            "KLS-001",
        )

    def test_product_code_is_carried_to_every_chunk_for_that_product(self):
        merino = next(product for product in get_catalog() if product["id"] == "merino")
        chunks = HybridRetriever._chunk_with_product_codes(catalog_document(merino))
        merino_chunks = [code for chunk, code in chunks if "Merinovillapaita Klassik" in chunk or "KLS-001" in chunk]
        self.assertTrue(merino_chunks)
        self.assertTrue(all(code == "KLS-001" for code in merino_chunks))

    def test_shared_catalogue_products_are_available_to_bm25_without_embedding_them(self):
        class FakeCollection:
            documents = ["TUOTE KLS-001: Merinovillapaita Klassik\nTuotekoodi: KLS-001"]
            ids = ["existing-vector-product"]

            def get(self, ids=None, include=None):
                selected = list(zip(self.ids, self.documents))
                if ids is not None:
                    selected = [item for item in selected if item[0] in ids]
                return {
                    "ids": [item[0] for item in selected],
                    "documents": [item[1] for item in selected],
                    "metadatas": [{} for _ in selected],
                }

            def count(self):
                return len(self.ids)

        retriever = object.__new__(HybridRetriever)
        retriever.collection = FakeCollection()
        retriever._rebuild_bm25()

        ranked = retriever._bm25_ranked_ids("pellavamekko Aava Natural", 10)
        catalog_id = "catalog-KOV-009"
        self.assertIn(catalog_id, ranked)
        result = retriever._fetch_ranked([catalog_id], {catalog_id: 1.0})[0]
        self.assertIn("Pellavamekko Aava", result[0])
        self.assertEqual(result[1]["source"], "catalog.json")
        self.assertEqual(retriever.get_vector_count(), 1)
        self.assertEqual(retriever.get_count(), 19)

        class EmptyCollection(FakeCollection):
            documents = []
            ids = []

        empty_index = object.__new__(HybridRetriever)
        empty_index.collection = EmptyCollection()
        empty_index._rebuild_bm25()
        self.assertEqual(empty_index.retrieve_for_evaluation("pellavamekko", method="hybrid")[0][1]["source"], "catalog.json")


if __name__ == "__main__":
    unittest.main()
