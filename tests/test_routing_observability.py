import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.planner import Planner
from src.router.confidence_gate import ConfidenceGate
from src.router.smart_router import SmartRouter


class FakeMemory:
    def __init__(self, result=None):
        self.result = result
        self.saved = []

    def find(self, question):
        return self.result

    def save(self, **decision):
        self.saved.append(decision)


class FakeSemanticRouter:
    def __init__(self, result):
        self.result = result

    def route(self, question):
        return dict(self.result)


class RoutingObservabilityTests(unittest.TestCase):
    def make_router(self, memory_result, semantic_result):
        router = SmartRouter.__new__(SmartRouter)
        router.memory = FakeMemory(memory_result)
        router.semantic = FakeSemanticRouter(semantic_result)
        router.confidence_gate = ConfidenceGate(0.80)
        return router

    def test_semantic_high_confidence_route_is_logged(self):
        router = self.make_router(
            None,
            {"intent": "RAG", "score": 0.91, "method": "SEMANTIC"},
        )

        with patch("src.router.smart_router.log") as log:
            result = router.route("Explain closure SOP")

        self.assertEqual(result["intent"], "RAG")
        self.assertEqual(result["method"], "SEMANTIC")
        self.assertEqual(result["score"], 0.91)
        self.assertEqual(result["memory"], "MISS")
        self.assertTrue(
            any("ConfidenceGate PASS" in call.args[1] for call in log.call_args_list)
        )

    def test_low_confidence_route_falls_back_and_is_logged(self):
        router = self.make_router(
            None,
            {"intent": "SQL", "score": 0.32, "method": "SEMANTIC"},
        )

        with patch("src.router.smart_router.log") as log:
            result = router.route("uncertain request")

        self.assertIsNone(result["intent"])
        self.assertEqual(result["method"], "FALLBACK")
        self.assertEqual(result["score"], 0.32)
        self.assertTrue(
            any("method=FALLBACK" in call.args[1] for call in log.call_args_list)
        )

    def test_memory_hit_returns_cached_route_and_is_logged(self):
        router = self.make_router(
            {"intent": "CHAT", "confidence": 0.99, "source": "NEMOTRON"},
            {"intent": "SQL", "score": 0.91, "method": "SEMANTIC"},
        )

        with patch("src.router.smart_router.log") as log:
            result = router.route("Hi")

        self.assertEqual(result["intent"], "CHAT")
        self.assertEqual(result["method"], "MEMORY")
        self.assertEqual(result["memory"], "HIT")
        self.assertTrue(
            any("RouteMemory HIT" in call.args[1] for call in log.call_args_list)
        )

    def test_planner_retains_nemotron_fallback_route(self):
        planner = Planner.__new__(Planner)
        planner.validator = SimpleNamespace(
            validate=lambda question, intent: {"decision": "PASS"}
        )
        planner.smart_router = SimpleNamespace(
            route=lambda question: {
                "intent": None,
                "score": 0.20,
                "method": "FALLBACK",
                "memory": "MISS",
            },
            save_nemotron_decision=lambda question, intent: None,
        )
        planner.last_route = None

        with patch("src.planner.router") as model_router, patch("src.planner.log"):
            model_router.planner.return_value.invoke.return_value.content = "SQL"
            intent = planner.plan("uncertain request")

        self.assertEqual(intent, "SQL")
        self.assertEqual(
            planner.last_route,
            {
                "intent": "SQL",
                "score": 0.20,
                "method": "NEMOTRON",
                "memory": "MISS",
            },
        )


if __name__ == "__main__":
    unittest.main()
