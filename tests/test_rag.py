from src.tools.rag_tool import rag_tool

print(
    rag_tool.invoke(
        "What is the SOP for damaged shipment?"
    )
)