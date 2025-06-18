# ReAct Agent Implementation

**Attribution:**
This code is based on materials from the AI Agents in LangGraph course by DeepLearning.AI, which itself is based on [Simon Willison's Python ReAct pattern](https://til.simonwillison.net/llms/python-react-pattern).

This project implements a ReAct (Reasoning and Acting) agent that combines reasoning and acting in an interleaved manner. The agent uses GPT-4 to process questions and can perform specific actions like calculations and retrieving dog weight information.

## Project Structure
- `main.py`: Contains the complete implementation including:
  - `Agent` class for handling conversations
  - Action implementations (calculate, average_dog_weight)
  - Query processing and execution logic
- `requirements.txt`: Project dependencies
- `tests/`: Test cases directory

## Features
- ReAct pattern implementation (Reasoning and Acting)
- Support for multiple actions:
  - `calculate`: Performs mathematical calculations
  - `average_dog_weight`: Returns average weights for different dog breeds
- Conversation memory and context management
- Integration with OpenRouter's deepseek/deepseek-r1-0528-qwen3-8b:free model

## Setup
1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your OpenRouter API key:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Usage
The main script includes an example query that demonstrates the agent's capabilities:

```python
from main import Agent, load_dotenv_and_init_client, query

# Initialize the OpenRouter and Tavily clients
load_dotenv_and_init_client()

# Create an agent instance
agent = Agent(prompt)  # prompt is defined in main.py

# Ask a question
question = "I have 2 dogs, a border collie and a scottish terrier. What is their combined weight?"
query(question, agent)
```

The agent will:
1. Process the question
2. Use reasoning to determine required actions
3. Execute actions and observe results
4. Provide a final answer

## Available Actions
- `calculate`: Perform mathematical calculations
  - Example: `calculate: 4 * 7 / 3`
- `average_dog_weight`: Get average weight for dog breeds
  - Example: `average_dog_weight: Collie`
  - Supported breeds: Scottish Terrier, Border Collie, Toy Poodle
