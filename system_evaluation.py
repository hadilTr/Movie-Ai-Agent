import time
from main import run_query_with_tools 
# Define your test scenarios
test_scenarios = [
    {
        "query": "Find all movies directed by Christopher Nolan",
        "expected_result": ["Inception", "Interstellar", "Dunkirk"]
    },
    {
        "query": "Retrieve actors in 'Inception' and their roles",
        "expected_result": ["Leonardo DiCaprio", "Joseph Gordon-Levitt", "Ellen Page"]
    },
    {
        "query": "List all awards won by movies released in 2010",
        "expected_result": ["Oscar Best Cinematography", "Oscar Best Sound Editing"]
    }
]

# Function to compare results
def check_correctness(agent_result, expected_result):
    # simple comparison (can improve for fuzzy matching)
    return set(agent_result) == set(expected_result)

# Run evaluation
results = []

for scenario in test_scenarios:
    query = scenario["query"]
    expected = scenario["expected_result"]
    
    start_time = time.time()
    agent_result, tool_used = run_query_with_tools(query)  # assumes your agent returns result and tool used
    end_time = time.time()
    
    correct = check_correctness(agent_result, expected)
    latency = round(end_time - start_time, 3)
    
    results.append({
        "Query": query,
        "Expected": expected,
        "Agent Result": agent_result,
        "Tool Used": tool_used,
        "Correct": correct,
        "Latency(s)": latency
    })

# Print results
for r in results:
    print(f"Query: {r['Query']}")
    print(f"Expected: {r['Expected']}")
    print(f"Agent Result: {r['Agent Result']}")
    print(f"Tool Used: {r['Tool Used']}")
    print(f"Correct: {r['Correct']}")
    print(f"Latency: {r['Latency(s)']}s")
    print("-"*50)
