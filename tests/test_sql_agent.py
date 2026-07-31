from src.sql_agent_old import SQLAgent

agent = SQLAgent()

question = input("Ask a database question: ")

answer = agent.ask(question)

print("\nAnswer:\n")
print(answer)