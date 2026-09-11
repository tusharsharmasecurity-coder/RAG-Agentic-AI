import time

from src.planner_engine import PlannerEngine
from src.logger import log
from src.supervisor.supervisor import Supervisor
from src.question_normalizer import QuestionNormalizer
from src.quality.checker import QualityChecker
from src.agents.orchestrator import AgentOrchestrator
from src.monitoring.metrics import MetricsCollector


class DelhiveryAgent:

    def __init__(self):

        # ========================================================
        # CORE COMPONENTS
        # ========================================================

        self.planner = PlannerEngine()
        self.metrics = MetricsCollector()

        # Share the same ChatMemory with Supervisor
        self.supervisor = Supervisor(chat_memory=self.planner.memory)

        # Sprint 6 multi-agent orchestrator
        self.orchestrator = AgentOrchestrator(self.supervisor)

        self.normalizer = QuestionNormalizer()

        self.quality = QualityChecker()

        log("AGENT", "Ready")

    # ============================================================
    # MAIN AGENT ENTRY POINT
    # ============================================================

    # ============================================================
    # MAIN AGENT ENTRY POINT
    # ============================================================

    def ask(self, question, thread_id="default_user"):
        total_start = time.time()

        # ========================================================
        # SAVE USER MESSAGE
        # ========================================================
        try:
            # Try to save to specific thread memory
            self.planner.memory.add_user(question, thread_id=thread_id)
        except TypeError:
            # Fallback if memory class doesn't accept thread_id yet
            self.planner.memory.add_user(question)

        # ========================================================
        # PLANNING
        # ========================================================
        planner_start = time.time()
        plan = self.planner.create_plan(question)
        planner_time = time.time() - planner_start

        print(f"Planner: {planner_time:.2f}s")
        intent = plan.get("intent", "CHAT")
        log("PLANNER", f"Intent = {intent}")

        print("\n========== AGENT PLAN ==========")
        print(f"Intent : {intent}")
        print(f"Tools  : {plan.get('tools', [])}")

        # ========================================================
        # MULTI-AGENT ORCHESTRATION
        # ========================================================
        orchestration_start = time.time()
        try:
            # Pass thread_id into the orchestrator/LangGraph for state management
            try:
                result = self.orchestrator.execute(
                    plan=plan,
                    question=question,
                    normalizer=self.normalizer,
                    thread_id=thread_id,
                )
            except TypeError:
                # Fallback if orchestrator execute doesn't accept thread_id yet
                result = self.orchestrator.execute(
                    plan=plan, question=question, normalizer=self.normalizer
                )
        except Exception as exc:
            log("AGENT", f"Orchestrator error: {exc}")
            return {
                "answer": "The agent encountered an execution error.",
                "tool_result": {
                    "type": "error",
                    "message": str(exc),
                },
                "intent": intent,
                "execution_time": round(time.time() - total_start, 4),
            }

        orchestration_time = time.time() - orchestration_start

        self.metrics.record(
            question=question,
            intent=result.get("intent", intent),
            total_time=time.time() - total_start,
            planner_time=planner_time,
            orchestration_time=orchestration_time,
            success=True,
        )

        # ========================================================
        # RESULT
        # ========================================================
        answer = result.get("answer", "No response generated.")
        tool_result = result.get("tool_result")
        result_intent = result.get("intent", intent)

        # ========================================================
        # SAVE AI RESPONSE
        # ========================================================
        try:
            try:
                self.planner.memory.add_ai(answer, thread_id=thread_id)
            except TypeError:
                self.planner.memory.add_ai(answer)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            log("AGENT", f"Chat memory save failed: {exc}")

        # ========================================================
        # QUALITY CHECK
        # ========================================================
        try:
            quality_result = self.quality.check(question, answer)
        except Exception:
            quality_result = None

        # ========================================================
        # TOTAL TIMING
        # ========================================================
        total_time = time.time() - total_start
        print("\n========== AGENT RESULT ==========")
        print(f"Intent        : {result_intent}")
        print(f"Planner time  : {planner_time:.3f}s")
        print(f"Agent time    : {orchestration_time:.3f}s")
        print(f"Total time    : {total_time:.3f}s")

        # ========================================================
        # FINAL RESPONSE
        # ========================================================
        response = {
            "answer": answer,
            "tool_result": tool_result,
            "intent": result_intent,
            "execution_time": round(total_time, 4),
        }

        if quality_result is not None:
            response["quality"] = quality_result

        return response
