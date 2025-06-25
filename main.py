import openai
import re
import os
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# Global OpenRouter client
client = None
# Global Tavily client
tavily_client = None


def search_tavily(query):
    if tavily_client is None:
        raise Exception("Tavily client not initialized. Call load_dotenv_and_init_client() first.")
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
                "OpenRouter client not initialized. Call load_dotenv_and_init_client() first.")
        completion = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            temperature=0,
            messages=self.messages)
        # Return message it gets back from the LLM
        return completion.choices[0].message.content


prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

average_dog_weight:
e.g. average_dog_weight: Collie
returns average weight of a dog when given the breed

search:
e.g. search: What is the capital of France?
Searches the web using Tavily and returns relevant information

Example session:

Question: What is the population of Paris?
Thought: I should search for information about Paris's population
Action: search: What is the current population of Paris, France?
PAUSE

You will be called again with this:

Observation: [Search results about Paris population]

You then output:

Answer: Based on the search results, Paris has a population of approximately 2.2 million people.
""".strip()


def calculate(what):
    return eval(what)


def average_dog_weight(name):
    if "Scottish Terrier" in name:
        return "Scottish Terriers average 20 lbs"
    elif "Border Collie" in name:
        return "a Border Collies average weight is 37 lbs"
    elif "Toy Poodle" in name:
        return "a toy poodles average weight is 7 lbs"
    else:
        return "An average dog weights 50 lbs"

# Create a dictionary of known actions
known_actions = {
    "calculate": calculate,
    "average_dog_weight": average_dog_weight,
    "search": search_tavily
}

action_re = re.compile(r'^Action: (\w+): (.*)$')


def query(question, agent, max_turns=5):
    print(f"Question: {question}\n")
    next_prompt = question
    for i in range(max_turns):
        result = agent(next_prompt)
        print(f"--- Turn {i+1} ---")
        print(result)
        actions = [action_re.match(a) for a in result.split(
            '\n') if action_re.match(a)]
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
            "OPENROUTER_API_KEY not found in .env file or environment variables.")
    if not tavily_api_key:
        raise ValueError(
            "TAVILY_API_KEY not found in .env file or environment variables.")
            
    client = OpenAI(api_key=api_key, base_url="https://openrouter.ai/api/v1")
    tavily_client = TavilyClient(tavily_api_key)


if __name__ == "__main__":
    load_dotenv_and_init_client()

    # Example of a direct chat completion (from the notebook)
    # print("Testing direct chat completion:")
    # chat_completion = client.chat.completions.create(
    #     model="gpt-4.0-mini",
    #     messages=[{"role": "user", "content": "Hello world"}]
    # )
    # print(chat_completion.choices[0].message.content)
    # print("---\n")

    agent_instance = Agent(prompt)

    # Main example query from the notebook
    main_question = "I have 2 dogs, a border collie and a scottish terrier. What is their combined weight?"
    query(main_question, agent_instance)

    # You can add other test calls from the notebook here if needed, for example:
    # print("\n--- Another Example ---")
    # agent_instance_2 = Agent(prompt)
    # result_poodle = agent_instance_2("How much does a toy poodle weigh?")
    # print(result_poodle)
    # if action_re.match(result_poodle.split('\n')[-1]): # Check if last line is an action
    #     action, action_input = action_re.match(result_poodle.split('\n')[-1]).groups()
    #     observation = known_actions[action](action_input)
    #     print(f"Observation: {observation}")
    #     next_prompt_poodle = f"Observation: {observation}"
    #     print(agent_instance_2(next_prompt_poodle))
