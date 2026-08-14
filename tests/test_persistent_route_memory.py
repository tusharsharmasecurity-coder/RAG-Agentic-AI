import unittest

from src.router.confidence_gate import ConfidenceGate
from src.router.route_memory import RouteMemory
from src.router.smart_router import SmartRouter
from src.text_normalizer import normalize


class FakeSemanticRouter:
    def __init__(self, result):
        self.result = result
        self.calls = 0

    def route(self, question):
        self.calls += 1
        return dict(self.result)


class PersistentRouteMemoryTests(unittest.TestCase):
    question = "How many shipments?"
    different_question = "Explain closure SOP"

    def setUp(self):
        self.memory = RouteMemory()
        self._delete_question(self.question)
        self._delete_question(self.different_question)

    def tearDown(self):
        self._delete_question(self.question)
        self._delete_question(self.different_question)

    def _delete_question(self, question):
        self.memory.db.cursor.execute(
            "DELETE FROM route_memory WHERE normalized_question = %s",
            (normalize(question),),
        )
        self.memory.db.connection.commit()

    @staticmethod
    def make_router(memory, semantic):
        router = SmartRouter.__new__(SmartRouter)
        router.memory = memory
        router.semantic = semantic
        router.confidence_gate = ConfidenceGate(0.80)
        return router

    def test_first_request_is_semantic_miss_then_saved(self):
        semantic = FakeSemanticRouter(
            {"intent": "SQL", "score": 0.95, "method": "SEMANTIC"}
        )
        router = self.make_router(self.memory, semantic)

        result = router.route(self.question)

        self.assertEqual(result["method"], "SEMANTIC")
        self.assertEqual(result["intent"], "SQL")
        self.assertEqual(semantic.calls, 1)
        self.assertEqual(self.memory.find(self.question)["intent"], "SQL")

    def test_same_request_hits_memory_without_semantic_router(self):
        self.memory.save(self.question, "SQL", 0.95, "SEMANTIC")
        semantic = FakeSemanticRouter(
            {"intent": "RAG", "score": 0.95, "method": "SEMANTIC"}
        )
        router = self.make_router(self.memory, semantic)

        result = router.route(self.question)

        self.assertEqual(result["method"], "MEMORY")
        self.assertEqual(result["intent"], "SQL")
        self.assertEqual(semantic.calls, 0)

    def test_new_memory_instance_hits_mysql(self):
        self.memory.save(self.question, "SQL", 0.95, "SEMANTIC")

        restarted_memory = RouteMemory()

        self.assertEqual(restarted_memory.find("how many shipment")["intent"], "SQL")

    def test_different_question_is_a_miss(self):
        self.memory.save(self.question, "SQL", 0.95, "SEMANTIC")

        self.assertIsNone(self.memory.find(self.different_question))


if __name__ == "__main__":
    unittest.main()
