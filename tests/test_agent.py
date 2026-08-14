from src.agent import DelhiveryAgent


def run_agent():
    agent = DelhiveryAgent()

    while True:
        question = input("\nYou : ")

        if question.lower() == "exit":
            break

        response = agent.ask(question)

        print("\n====================")
        print(response)
        print("====================")


if __name__ == "__main__":
    run_agent()