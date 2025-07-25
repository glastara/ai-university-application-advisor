import openai
import re
import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient
import json

# Global OpenRouter client
client = None
# Global Tavily client
tavily_client = None


def search_tavily(query):
    if tavily_client is None:
        raise Exception(
            "Tavily client not initialized. Call load_dotenv_and_init_client() first."
        )
    response = tavily_client.search(query)
    return response


class Agent:
    # Initialise the agent with a system prompt
    def __init__(self, system=""):
        # Save system prompt
        self.system = system
        # Initialise messages list
        self.messages = []
        # If system prompt is not empty, add it to messages
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def save_history(self, filename="history.json"):
        with open(filename, "w") as f:
            json.dump(self.messages, f)

    def load_history(self, filename="history.json"):
        try:
            with open(filename, "r") as f:
                self.messages = json.load(f)
        except FileNotFoundError:
            pass  # No history to load, start fresh

    # Call the agent with a message
    def __call__(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    # Execute the agent
    def execute(self):
        if client is None:
            raise Exception(
                "OpenRouter client not initialized. Call load_dotenv_and_init_client() first."
            )
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            temperature=0.2,
            messages=self.messages,
        )
        # Return message it gets back from the LLM
        return completion.choices[0].message.content


prompt = """
You are an expert University Application Advisor specialising in UK higher education. Your role is to help students find suitable courses and provide guidance on their university applications.

You operate in a ReAct loop: Thought → Action → PAUSE → Observation → Answer.

Your available actions are:

search:
e.g. search: "Computer Science courses UK universities 2026"
Searches the web for current course information (e.g. course fees, module options), university rankings, entry requirements, and application deadlines

calculate:
e.g. calculate: (85 + 92) / 2
Performs calculations for grade averages, UCAS points, or other numerical assessments

Example session:

Question: I want to study Computer Science in the UK. I have A-levels in Maths (A), Physics (B), and English (C). What courses should I consider?

Thought: I need to search for Computer Science courses in UK universities and understand typical entry requirements for this subject.
Action: search: "Computer Science degree courses UK universities entry requirements A-levels 2026"
PAUSE

You will be called again with this:

Observation: [Search results about Computer Science courses and entry requirements]

You then output:

Thought: Based on the search results, I can see typical entry requirements and available courses. Let me calculate the student's UCAS points and provide specific recommendations.
Action: calculate: (120 + 40 + 32)
PAUSE

You will be called again with this:

Observation: 192

You then output:

Answer: Based on your A-level grades (Maths A=120, Physics B=40, English C=32), you have 192 UCAS points. For Computer Science in the UK, I recommend considering:

1. [University Name] - BSc Computer Science (Entry: AAB/ABB, 136-128 points)
2. [University Name] - Computer Science with AI (Entry: AAB, 136 points)

Focus areas for your application:
- Highlight your strong Maths grade (A) as it's crucial for Computer Science
- Consider retaking English to improve your overall profile
- Gain programming experience through online courses or projects
- Research specific universities' course structures and specializations

Guidelines for your responses:
- Always search for current, up-to-date information.
- If you do not know a specific number (such as a deposit amount), say you do not know or suggest the user check the official university website.
- Do not make up or guess specific fees, dates, or requirements.
- Provide specific course recommendations with entry requirements
- Calculate UCAS points when relevant
- Give actionable advice on application focus areas
- Consider the student's academic background and interests
- Mention application deadlines and important dates when found
- Suggest alternative courses or pathways when appropriate
""".strip()


def calculate(what):
    return eval(what)


# Create a dictionary of known actions
known_actions = {"calculate": calculate, "search": search_tavily}

action_re = re.compile(r"^Action: (\w+): (.*)$")


def query(question, agent, max_turns=5):
    print(f"Question: {question}\n")
    next_prompt = question
    for i in range(max_turns):
        result = agent(next_prompt)
        # Save history after each turn
        agent.save_history()
        print(f"--- Turn {i + 1} ---")
        print(result)
        actions = [action_re.match(a) for a in result.split("\n") if action_re.match(a)]
        if actions:
            action, action_input = actions[0].groups()
            if action not in known_actions:
                print(f"Unknown action: {action}: {action_input}")
                return
            print(f"Action: {action}('{action_input}')")
            observation = known_actions[action](action_input)
            print(f"Observation: {observation}\n")
            next_prompt = f"Observation: {observation}"
        else:
            # If no action, the result might be the final answer or need further parsing
            if result.startswith("Answer:"):
                print(f"\nFinal Answer: {result.split('Answer: ', 1)[1]}")
            else:
                print("No action taken and no clear answer. Stopping.")
            return
    print("Max turns reached.")


def load_dotenv_and_init_client():
    global client, tavily_client
    _ = load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        raise ValueError(
            "OPENROUTER_API_KEY not found in .env file or environment variables."
        )
    if not tavily_api_key:
        raise ValueError(
            "TAVILY_API_KEY not found in .env file or environment variables."
        )

    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    tavily_client = TavilyClient(tavily_api_key)


def is_question(user_input):
    # List of question words
    question_words = [
        "who",
        "what",
        "when",
        "where",
        "why",
        "how",
        "which",
        "can",
        "is",
        "are",
        "do",
        "does",
        "did",
        "will",
        "could",
        "would",
        "should",
    ]
    # Lowercase input for easier matching
    input_lower = user_input.lower().strip()
    # Check for question word anywhere in the input
    for word in question_words:
        if re.search(rf"\b{word}\b", input_lower):
            return True
    # Optionally, filter out known non-question statements ending with '?'
    non_questions = ["i have no more questions", "that's all", "no more questions"]
    for statement in non_questions:
        if input_lower.startswith(statement) and input_lower.endswith("?"):
            return False
    # If it ends with a question mark, treat as a question (unless filtered above)
    if input_lower.endswith("?"):
        return True
    return False


if __name__ == "__main__":
    load_dotenv_and_init_client()
    agent_instance = Agent(prompt)
    agent_instance.load_history()

    print("Welcome to your University Application Advisor!")
    print(
        "Ask your question below. (Write 'exit' to exit. If you don't type a question, I'll end the conversation for you.)"
    )

    while True:
        user_input = input("\nAsk a question:\n> ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        if not user_input:
            print("It looks like you have no questions for now. Goodbye.")
            break
        if is_question(user_input):
            query(user_input, agent_instance)
        else:
            print("It looks like you have no questions for now. Goodbye.")
            break

    # Can add other test calls here if needed, for example:
    # print("\n--- Another Example ---")
    # agent_instance_2 = Agent(prompt)
    # result_engineering = agent_instance_2("I'm interested in Mechanical Engineering. I have A-levels in Maths (A), Physics (A), and Chemistry (B). What are my options?")
    # print(result_engineering)
