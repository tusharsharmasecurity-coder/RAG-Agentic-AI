import json

from src.prompt import CHART_SYSTEM_PROMPT
from src.models.router import ModelRouter

router = ModelRouter()


class VisualizationAgent:

    def decide(self, dataframe):

        columns = list(dataframe.columns)

        prompt = CHART_SYSTEM_PROMPT.format(
            columns=columns
        )

        response = router.dashboard().invoke(prompt)

        try:

            return json.loads(response.content)

        except:

            return {
                "chart": "table",
                "reason": "Fallback"
            }