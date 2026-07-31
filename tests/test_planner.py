from src.planner import Planner

planner = Planner()

questions = [

    "How many customers cut the call in ajio?",

    "Explain the SOP for damaged shipment.",

    "How many delayed shipments and explain delay policy.",

    "Hello"
]

for q in questions:

    print(q)

    print("->", planner.plan(q))

    print()