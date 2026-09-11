from src.tools.sql_tool import sql_tool
from src.tools.workspace_tool import workspace_tool
from src.agents.rag_agent import RAGAgent
from src.analytics.dataframe_agent import DataFrameAgent
from src.models.router import ModelRouter

router = ModelRouter()


class Supervisor:

    def __init__(self, chat_memory=None):
        self.rag = RAGAgent()
        self.df = DataFrameAgent()
        self.chat_memory = chat_memory

    def sql(self, question):
        return sql_tool.invoke({"question": question})

    def rag_search(self, question):
        return self.rag.ask(question)

    def dataframe(self, question):
        return self.df.run(question)

    def workspace(self, action: str, query: str = "", sheet_id: str = ""):
        return workspace_tool.invoke({
            "action": action,
            "query": query,
            "sheet_id": sheet_id
        })

    def chat(self, prompt):
        return router.chat().invoke(prompt).content

    def chat_memory_context(self):
        if self.chat_memory is None:
            return ""
        return self.chat_memory.get_context()