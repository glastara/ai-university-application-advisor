# AI University Application Advisor (ReAct Agent)

**Attribution:**
This code is based on materials from the AI Agents in LangGraph course by DeepLearning.AI, which itself is based on [Simon Willison's Python ReAct pattern](https://til.simonwillison.net/llms/python-react-pattern).

This project implements a ReAct (Reasoning and Acting) agent that acts as an expert University Application Advisor specialising in UK higher education. The agent combines reasoning and acting to help students find suitable courses and provide guidance on their university applications using real-time web search capabilities.

This repository also serves as a lightweight MVP for my AI university application advisor business, [Anyverse](https://www.anyverse.app).

## Project Structure
- `main.py`: Contains the complete implementation including:
  - `Agent` class for handling conversations
  - Action implementations (calculate, search)
  - Query processing and execution logic
  - University advisor prompt and guidelines
- `requirements.txt`: Project dependencies
- `tests/`: Test cases directory

## Features
- **ReAct pattern implementation** (Reasoning and Acting)
- **Real-time web search** using Tavily for current course information
- **UCAS points calculation** for UK university applications
- **Course recommendations** with entry requirements
- **Application guidance** and focus areas
- **Conversation memory** and context management
- **Integration with OpenRouter** using deepseek/deepseek-r1-0528-qwen3-8b:free model

## Available Actions
- `search`: Searches the web for current course information, university rankings, entry requirements, and application deadlines
  - Example: `search: "Computer Science courses UK universities 2026"`
- `calculate`: Performs calculations for grade averages, UCAS points, or other numerical assessments
  - Example: `calculate: (120 + 40 + 32)` for UCAS points calculation

## Setup
1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with your API keys:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

## Usage
The main script includes an example query that demonstrates the agent's capabilities:

```python
from main import Agent, load_dotenv_and_init_client, query

# Initialise the OpenRouter and Tavily clients
load_dotenv_and_init_client()

# Create an agent instance
agent = Agent(prompt)  # prompt is defined in main.py

# Ask a question about university applications
question = "I want to study Computer Science in the UK. I have A-levels in Maths (A), Physics (B), and English (C). What courses should I consider?"
query(question, agent)
```

The agent will:
1. Process the student's academic background and interests
2. Search for current course information and entry requirements
3. Calculate UCAS points and assess eligibility
4. Provide specific course recommendations
5. Give actionable advice on application focus areas

## Example Output
The agent provides comprehensive responses including:
- **Course recommendations** with specific universities and entry requirements
- **UCAS points calculations** based on A-level grades
- **Application focus areas** and improvement suggestions
- **Current information** about courses, fees, and deadlines
- **Alternative pathways** when appropriate

## Supported Queries
The agent can help with:
- Course recommendations for any subject
- Entry requirement analysis
- UCAS points calculations
- Application strategy advice
- University rankings and comparisons
- Course structure and module information
- Application deadlines and important dates

## API Requirements
- **OpenRouter API Key**: For accessing the DeepSeek model
- **Tavily API Key**: For real-time web search capabilities

Both services offer free tiers suitable for testing and development (trust me, I checked — very broke at the time of making this).

## Testing

You can run the test suite using pytest. Ensure dependencies are installed (pytest is included in `requirements.txt`).

1. Install dependencies (inside your virtual environment):
```bash
pip install -r requirements.txt
```

2. Run all tests (recommended):
```bash
python3 -m pytest -q
```

3. Run tests for a single file (this repository uses `test_main.py`):
```bash
python3 -m pytest -q test_main.py
```

4. See which tests ran, their names, and pass/fail status (recommended):
```bash
python3 -m pytest -vv
```

Note: To also see print output from tests, append `-s` (e.g., `python3 -m pytest -vv -s`).

Notes:
- The tests include logic to exercise the ReAct loop using mock agents and stubbed search calls, so no external API calls are made during testing.
- To run just a single test function, you can use the `-k` flag, for example:
```bash
python3 -m pytest -k test_query_flow_with_mock_agent_calculate -vv -s
```

## Suggested improvements

This project is an MVP built with a free model, so responses can be slow and there is plenty of room for improvement. Ideas for future contributors:
- Improve response speed (currently approx 30 secs) and quality by using a stronger model and enabling streaming output.
- Add more assertions and structured checks in tests (beyond prints) and increase coverage.
- Introduce retries and backoff for network calls; cache stable lookups; normalise citation formats.
- Expand qualification handling (IB, BTEC, Scottish qualifications) and verified equivalency lookups.
- Enhance the ReAct loop with stricter output validation and better error handling on missing observations.
- Add configuration for year of entry, fee status, and subject preferences; persist user profile between runs.
- Provide a lightweight UI (CLI flags or simple web UI) for easier use.
- Add pre-commit hooks (formatting, linting, security/secret scans) and CI to run tests automatically.

This repository intentionally uses UK English throughout.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
