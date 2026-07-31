from src.dashboard.dashboard_agent import DashboardAgent

agent = DashboardAgent()

sample = {
    "columns": ["Warehouse", "Total"],
    "rows": [
        ("Ajio", 120),
        ("Purple", 90),
        ("Recovery", 40)
    ]
}

df = agent.build(sample)

print(df)