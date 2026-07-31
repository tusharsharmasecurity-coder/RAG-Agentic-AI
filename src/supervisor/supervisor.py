from src.tools.sql_tool import sql_tool
from src.agents.rag_agent import RAGAgent
from src.analytics.dataframe_agent import DataFrameAgent
from src.models.router import ModelRouter

router = ModelRouter()


class Supervisor:

    def __init__(self):

        self.rag = RAGAgent()

        self.df = DataFrameAgent()

    # ------------------------------

    def sql(self, question):

        return sql_tool.invoke(question)

    # ------------------------------

    def rag_search(self, question):

        return self.rag.ask(question)

    # ------------------------------

    def dataframe(self, question):

        return self.df.run(question)

    # ------------------------------

    def chat(self, prompt):

        return router.chat().invoke(prompt).content
