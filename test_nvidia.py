from src.models.router import ModelRouter

router = ModelRouter()

response = router.planner().invoke(
    "Return ONLY the word SQL."
)

print(response.content)