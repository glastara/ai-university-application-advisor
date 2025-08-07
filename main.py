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
            "Tavily client not initialised. Call load_dotenv_and_init_client() first."
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
                "OpenRouter client not initialised. Call load_dotenv_and_init_client() first."
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
Action: calculate: (48 + 40 + 32)
PAUSE

You will be called again with this:

Observation: 120

You then output:

Answer: Based on your A-level grades (Maths A=48, Physics B=40, English C=32), you have 120 UCAS points. For Computer Science in the UK, I recommend considering:

1. [University Name] - BSc Computer Science (Entry: AAB/ABB, 136-128 points)
2. [University Name] - Computer Science with AI (Entry: AAB, 136 points)

Focus areas for your application:
- Highlight your strong Maths grade (A) as it's crucial for Computer Science
- Consider retaking English to improve your overall profile
- Gain programming experience through online courses or projects
- Research specific universities' course structures and specialisations

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


def safe_calculate(expression):
    """Safely evaluate mathematical expressions without using eval()"""
    try:
        # Remove any whitespace
        expression = expression.strip()
        
        # Check if this looks like a mathematical expression
        # Allow more characters but still block dangerous ones
        dangerous_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_[]{}|\\`~@#$%^')
        if any(c in dangerous_chars for c in expression):
            raise ValueError("Expression contains potentially dangerous characters")
        
        # Allow mathematical and safe characters
        # This includes: numbers, basic operators, parentheses, spaces, dots, commas
        safe_chars = set('0123456789+-*/()., ')
        if not all(c in safe_chars for c in expression):
            # If it contains other characters, it might not be a math expression
            # Let's check if it's still safe to process
            other_chars = set(expression) - safe_chars
            if any(c in dangerous_chars for c in other_chars):
                raise ValueError("Expression contains potentially dangerous characters")
        
        # Use our safe parser for mathematical expressions
        if '(' in expression or ')' in expression:
            # Handle parentheses by evaluating inner expressions first
            return evaluate_expression(expression)
        else:
            # Simple arithmetic without parentheses
            return evaluate_simple_expression(expression)
    except Exception as e:
        return f"Error calculating: {str(e)}"


def evaluate_simple_expression(expr):
    """Evaluate simple arithmetic expressions without parentheses"""
    # Split by operators, preserving them
    import re
    parts = re.split(r'([+\-*/])', expr.replace(' ', ''))
    parts = [p for p in parts if p]
    
    if len(parts) == 1:
        return float(parts[0])
    
    # Handle multiplication and division first
    i = 1
    while i < len(parts) - 1:
        if parts[i] in ['*', '/']:
            left = float(parts[i-1])
            right = float(parts[i+1])
            if parts[i] == '*':
                result = left * right
            else:
                if right == 0:
                    raise ValueError("Division by zero")
                result = left / right
            parts[i-1:i+2] = [str(result)]
            i -= 1
        i += 2
    
    # Handle addition and subtraction
    result = float(parts[0])
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            if parts[i] == '+':
                result += float(parts[i+1])
            elif parts[i] == '-':
                result -= float(parts[i+1])
    
    return result


def evaluate_expression(expr):
    """Evaluate expressions with parentheses"""
    # Find innermost parentheses
    while '(' in expr:
        start = expr.rfind('(')
        end = expr.find(')', start)
        if end == -1:
            raise ValueError("Mismatched parentheses")
        
        inner_expr = expr[start+1:end]
        inner_result = evaluate_simple_expression(inner_expr)
        expr = expr[:start] + str(inner_result) + expr[end+1:]
    
    return evaluate_simple_expression(expr)


# Create a dictionary of known actions
known_actions = {"calculate": safe_calculate, "search": search_tavily}

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
        "who", "what", "when", "where", "why", "how", "which",
        "can", "is", "are", "do", "does", "did", "will", "could", "would", "should"
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


def get_ucas_points(grade, subject_type="A-level"):
    """Get UCAS points for a given grade and subject type"""
    ucas_points = {
        "A-level": {
            "A*": 56, "A": 48, "B": 40, "C": 32, "D": 24, "E": 16
        },
        "AS-level": {
            "A": 20, "B": 16, "C": 12, "D": 10, "E": 6
        },
        "BTEC": {
            "D*": 56, "D": 48, "M": 32, "P": 16
        }
    }
    
    try:
        return ucas_points.get(subject_type, {}).get(grade.upper(), 0)
    except:
        return 0

def calculate_ucas_total(grades_input):
    """Calculate total UCAS points from a list of grades"""
    try:
        # Parse input like "Maths A, Physics B, English C"
        grades = [g.strip() for g in grades_input.split(',')]
        total = 0
        breakdown = []
        
        for grade_entry in grades:
            if ' ' in grade_entry:
                subject, grade = grade_entry.rsplit(' ', 1)
                points = get_ucas_points(grade)
                total += points
                breakdown.append(f"{subject}: {grade} = {points} points")
        
        result = f"Total UCAS points: {total}\nBreakdown:\n" + "\n".join(breakdown)
        return result
    except Exception as e:
        return f"Error calculating UCAS points: {str(e)}"


if __name__ == "__main__":
    load_dotenv_and_init_client()
    agent_instance = Agent(prompt)
    agent_instance.load_history()

    print("Welcome to your University Application Advisor!")
    print("Ask your question below. (Write 'exit' to exit. If you don't type a question, I'll end the conversation for you.)")

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
