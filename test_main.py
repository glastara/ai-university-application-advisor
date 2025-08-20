#!/usr/bin/env python3
"""
Test script for the updated main.py functionality
"""

def test_ucas_points():
    """Test the UCAS points calculation functions"""
    from main import get_ucas_points, calculate_ucas_total
    
    print("=== TESTING UCAS POINTS CALCULATION ===\n")
    
    # Test individual grade points
    print("Testing individual grade points:")
    test_grades = [
        ("A*", "A-level"), ("A", "A-level"), ("B", "A-level"), 
        ("C", "A-level"), ("D", "A-level"), ("E", "A-level"),
        ("A", "AS-level"), ("B", "AS-level"), ("C", "AS-level")
    ]
    
    for grade, level in test_grades:
        points = get_ucas_points(grade, level)
        print(f"  {level} {grade} = {points} points")
    
    print("\nTesting grade list calculation:")
    test_grade_lists = [
        "Maths A, Physics B, English C",
        "Biology A*, Chemistry A, Maths A",
        "History B, Geography C, English D"
    ]
    
    for grade_list in test_grade_lists:
        result = calculate_ucas_total(grade_list)
        print(f"\nInput: {grade_list}")
        print(f"Result: {result}")

def test_safe_calculation():
    """Test the safe calculation function"""
    from main import safe_calculate
    
    print("\n=== TESTING SAFE CALCULATION ===\n")
    
    # Test valid mathematical expressions
    print("Testing valid mathematical expressions:")
    valid_tests = [
        ("2 + 3", 5.0),
        ("(48 + 40 + 32)", 120.0),
        ("10 * 5", 50.0),
        ("100 / 4", 25.0),
        ("(85 + 92) / 2", 88.5),
        ("1,000 + 500", 1500.0)
    ]
    
    for expression, expected in valid_tests:
        try:
            result = safe_calculate(expression)
            status = "✓" if result == expected else "✗"
            print(f"  {status} '{expression}' → {result} (expected: {expected})")
        except Exception as e:
            print(f"  ✗ '{expression}' → ERROR: {e}")
    
    # Test dangerous expressions (should be blocked)
    print("\nTesting dangerous expressions (should be blocked):")
    dangerous_tests = [
        "__import__('os').system('echo hacked')",
        "eval('2 + 3')",
        "open('secret.txt').read()",
        "2 + 3; __import__('os').listdir('.')"
    ]
    
    for expression in dangerous_tests:
        result = safe_calculate(expression)
        # Check if the result is an error message (starts with "Error calculating:")
        if isinstance(result, str) and result.startswith("Error calculating:"):
            print(f"  ✓ '{expression}' → BLOCKED: {result}")
        else:
            # If we get here, the dangerous code was NOT blocked - this is BAD
            print(f"  ✗ '{expression}' → {result} (SHOULD BE BLOCKED!)")

def test_agent_creation():
    """Test that the Agent class can be created"""
    from main import Agent, prompt
    
    print("\n=== TESTING AGENT CREATION ===\n")
    
    try:
        agent = Agent(prompt)
        print("✓ Agent created successfully")
        print(f"✓ System prompt length: {len(agent.system)} characters")
        print(f"✓ Messages list initialized: {len(agent.messages)} messages")
        
        # Test that the first message is the system prompt
        if agent.messages and agent.messages[0]["role"] == "system":
            print("✓ System prompt added to messages")
        else:
            print("✗ System prompt not found in messages")
            
    except Exception as e:
        print(f"✗ Error creating agent: {e}")

def test_question_detection():
    """Test the question detection function"""
    from main import is_question
    
    print("\n=== TESTING QUESTION DETECTION ===\n")
    
    test_questions = [
        ("What are the entry requirements?", True),
        ("How do I apply?", True),
        ("Can you help me?", True),
        ("I have no more questions?", False),
        ("Thank you", False),
        ("Goodbye", False),
        ("What is 2 + 2?", True),
        ("I need help with my application", False)
    ]
    
    for question, expected in test_questions:
        result = is_question(question)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{question}' → {result} (expected: {expected})")

def test_prompt_contract_and_content():
    """Validate that the updated system prompt includes key ReAct and citation instructions"""
    from main import prompt

    print("\n=== TESTING PROMPT CONTRACT AND CONTENT ===\n")

    required_fragments = [
        "You operate in a strict ReAct loop",
        "Action: calculate:",
        "Action: search:",
        "Answer:",
        "UCAS tariff",
        "A* = 56",
        "Include 2–4 citations",
        "Formatting for Answer:",
        "Error handling:",
    ]

    for fragment in required_fragments:
        contains = fragment in prompt
        status = "✓" if contains else "✗"
        print(f"  {status} prompt contains '{fragment}'")

def test_query_flow_with_mock_agent_calculate():
    """Exercise the query loop using a mock agent that returns a calculate action then a final answer"""
    from main import query

    print("\n=== TESTING QUERY FLOW (CALCULATE) WITH MOCK AGENT ===\n")

    class MockAgent:
        def __init__(self):
            self._responses = [
                "Thought: compute points\nAction: calculate: (48 + 40 + 32)\nPAUSE",
                "Answer: Your UCAS total is 120. Consider ABB–BBB courses.",
            ]
            self._idx = 0

        def __call__(self, message):
            resp = self._responses[min(self._idx, len(self._responses) - 1)]
            self._idx += 1
            return resp

        def save_history(self, filename="history.json"):
            pass

    mock_agent = MockAgent()
    query("Please recommend CS courses for A(48), B(40), C(32)", mock_agent, max_turns=3)

def test_query_flow_with_mock_agent_search():
    """Exercise the query loop using a mock agent that triggers a search action; monkeypatch search to avoid network"""
    from main import query, known_actions

    print("\n=== TESTING QUERY FLOW (SEARCH) WITH MOCK AGENT ===\n")

    original_search = known_actions.get("search")
    try:
        # Monkeypatch search to a deterministic stub
        known_actions["search"] = lambda q: {"results": [
            {"title": "Example University - BSc Computer Science", "url": "https://example.ac.uk"}
        ]}

        class MockAgent:
            def __init__(self):
                self._responses = [
                    "Thought: look up entry requirements\nAction: search: site:*.ac.uk \"Computer Science\" entry requirements 2026\nPAUSE",
                    "Answer: Based on the results, consider BBB–ABB courses and verify on official pages.",
                ]
                self._idx = 0

            def __call__(self, message):
                resp = self._responses[min(self._idx, len(self._responses) - 1)]
                self._idx += 1
                return resp

            def save_history(self, filename="history.json"):
                pass

        mock_agent = MockAgent()
        query("Find CS options around BBB", mock_agent, max_turns=3)
    finally:
        if original_search is not None:
            known_actions["search"] = original_search
