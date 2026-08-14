from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder


class SemanticIntentRouter:

    def __init__(self):

        self.encoder = HuggingFaceEncoder(
            name="sentence-transformers/all-MiniLM-L6-v2"
        )

        sql = Route(
            name="SQL",
            utterances=[
                "How many shipments?",
                "How many AWB?",
                "Total shipments",
                "Total AWB",
                "Shipment count",
                "Count shipments",
                "Average shipment weight",
                "Show shipments by warehouse",
            ],
        )

        rag = Route(
            name="RAG",
            utterances=[
                "Explain the closure SOP",
                "What is the closure policy?",
                "Explain the shipment process",
                "Show me the guidelines",
                "What does the SOP say?",
            ],
        )

        both = Route(
            name="BOTH",
            utterances=[
                "Show shipments affected by the closure policy",
                "Compare shipment data with the SOP",
                "How many shipments violated the policy?",
            ],
        )

        dataframe = Route(
            name="DATAFRAME",
            utterances=[
                "Sort this result",
                "Filter this result",
                "Show top 10 from this",
                "Plot this result",
                "Group this result",
            ],
        )

        chat = Route(
            name="CHAT",
            utterances=[
                "Hi",
                "Hello",
                "Hey",
                "Thanks",
                "Thank you",
                "Bye",
                "Good morning",
            ],
        )

        self.router = SemanticRouter(
            encoder=self.encoder,
            routes=[
                sql,
                rag,
                both,
                dataframe,
                chat,
            ],
            auto_sync="local",
        )

    def route(self, question: str):

        result = self.router(question)

        if result is None:
            return {
                "intent": None,
                "score": 0.0,
                "method": "SEMANTIC",
            }

        return {
            "intent": result.name,
            "score": result.similarity_score,
            "method": "SEMANTIC",
        }