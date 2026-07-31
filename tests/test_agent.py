from src.agent import DelhiveryAgent

agent = DelhiveryAgent()

while True:

    question = input("\nYou : ")

    if question.lower() == "exit":
        break

    response = agent.ask(question)

    print("\n====================")

    print(response)

    print("====================")