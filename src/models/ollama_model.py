from langchain_ollama import ChatOllama


def llm(model_name):

    return ChatOllama(
        model=model_name,
        temperature=0
    )