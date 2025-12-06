import time
from main import run_query_with_tools  # Import your agent's function


# ---------------------------
# Test Scenarios
# ---------------------------
test_scenarios = [
    {
        "query": "Find all movies directed by Christopher Nolan",
        "expected_result": ["Inception", "Interstellar"]
    }
   
]


# ---------------------------
# Correctness Check
# ---------------------------
def check_correctness(agent_result, expected_result):
    if not agent_result:
        return False

    # If the agent returns text, convert to lowercase comparison
    if isinstance(agent_result, str):
        agent_result = agent_result.lower()
        return all(item.lower() in agent_result for item in expected_result)

    # If the agent returns list (ideal)
    if isinstance(agent_result, list):
        return set(item.lower() for item in agent_result) == set(item.lower() for item in expected_result)

    return False


# ---------------------------
# Main Runner
# ---------------------------
def main():
    results = []

    for scenario in test_scenarios:
        query = scenario["query"]
        expected = scenario["expected_result"]

        print(f"Running: {query}")

        start_time = time.time()
        agent_result, tool_used = run_query_with_tools(query)
        end_time = time.time()

        correctness = check_correctness(agent_result, expected)
        latency = round(end_time - start_time, 3)

        results.append({
            "Query": query,
            "Expected": expected,
            "Agent Result": agent_result,
            "Tool Used": tool_used,
            "Correct": correctness,
            "Latency(s)": latency
        })

    print("\n=================== EVALUATION RESULTS ===================\n")
    for r in results:
        print(f"Query: {r['Query']}")
        print(f"Expected: {r['Expected']}")
        print(f"Agent Result: {r['Agent Result']}")
        print(f"Tool Used: {r['Tool Used']}")
        print(f"Correct: {r['Correct']}")
        print(f"Latency: {r['Latency(s)']}s")
        print("-" * 50)


if __name__ == "__main__":
    main()
