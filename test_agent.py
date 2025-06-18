from main import Agent, load_dotenv_and_init_client, query, prompt

def main():
    # Initialize the clients
    load_dotenv_and_init_client()

    # Create an agent instance
    agent = Agent(prompt)

    # Test questions that would benefit from web search
    questions = [
        "What are the latest developments in quantum computing?",
        "What is the current state of fusion energy research?",
        "What are the main differences between Python and JavaScript?"
    ]

    # Try each question
    for question in questions:
        print("\n" + "="*50)
        query(question, agent)

if __name__ == "__main__":
    main() 