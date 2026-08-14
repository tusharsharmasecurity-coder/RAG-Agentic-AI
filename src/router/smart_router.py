from src.logger import log
from src.router.confidence_gate import ConfidenceGate
from src.router.route_memory import RouteMemory
from src.router.semantic_router import SemanticIntentRouter


class SmartRouter:

    def __init__(self):
        self.memory = RouteMemory()
        self.semantic = SemanticIntentRouter()
        self.confidence_gate = ConfidenceGate()

    def route(self, question):
        memory_result = self.memory.find(question)
        memory_state = "HIT" if memory_result else "MISS"
        log("ROUTER", f"RouteMemory {memory_state}")

        if memory_result:
            cached_route = {
                "intent": memory_result["intent"],
                "score": memory_result["confidence"],
                "method": "MEMORY",
                "memory": memory_state,
            }
            gate_passed = self.confidence_gate.allows(cached_route)
            log(
                "ROUTER",
                "ConfidenceGate "
                f"{'PASS' if gate_passed else 'FAIL'} "
                f"intent={cached_route['intent']} score={cached_route['score']}",
            )

            if gate_passed:
                log(
                    "ROUTER",
                    f"intent={cached_route['intent']} method=MEMORY "
                    f"score={cached_route['score']}",
                )
                return cached_route

        semantic_result = self.semantic.route(question)
        semantic_result["memory"] = memory_state
        gate_passed = self.confidence_gate.allows(semantic_result)
        log(
            "ROUTER",
            "Semantic "
            f"intent={semantic_result['intent']} score={semantic_result['score']}",
        )
        log("ROUTER", f"ConfidenceGate {'PASS' if gate_passed else 'FAIL'}")

        if semantic_result["intent"] is not None and gate_passed:
            self.memory.save(
                question=question,
                intent=semantic_result["intent"],
                confidence=semantic_result["score"],
                method="SEMANTIC",
            )
            log(
                "ROUTER",
                f"intent={semantic_result['intent']} method=SEMANTIC "
                f"score={semantic_result['score']}",
            )
            return semantic_result

        fallback_result = {
            "intent": None,
            "score": semantic_result.get("score"),
            "method": "FALLBACK",
            "memory": memory_state,
        }
        log(
            "ROUTER",
            f"intent=None method=FALLBACK score={fallback_result['score']}",
        )
        return fallback_result

    def save_nemotron_decision(self, question, intent, confidence=1.0):
        self.memory.save(
            question=question,
            intent=intent,
            confidence=confidence,
            method="NEMOTRON",
        )
