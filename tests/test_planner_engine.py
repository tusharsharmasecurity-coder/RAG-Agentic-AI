import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.planner_engine import PlannerEngine

engine = PlannerEngine()

questions = [

    "How many shipments are delayed?",

    "Explain SOP for damages.",

    "How many delayed shipments and explain policy?",

    "Hello"

]

for q in questions:

    print(engine.create_plan(q))