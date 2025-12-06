from tools.graph_query_tool import query as graph_query
from tools.search_tool import vector_search
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from typing import TypedDict, Annotated, Sequence
from langchain_groq import ChatGroq
import operator
import time
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------
# LLM setup
# ---------------------------
llm = ChatGroq(
    api_key=os.getenv("groq_api_key"),
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ---------------------------
# System prompt (IMPROVED)
# ---------------------------
system_prompt = """You are a movie database assistant with access to a Neo4j graph database.

DATABASE SCHEMA:
- Nodes: movie (id, title, year, plot, plot_embedding), person (id, name, bio)
- Relationships: ACTED_IN, DIRECTED

TOOLS:
1. query: Execute Cypher queries for exact matches (titles, actors, directors, years)
2. vector_search: Semantic search using plot_embedding for themes/concepts

DECISION RULES:
- User asks for specific title/actor/director → Use query with Cypher
- User asks about themes/plot/concepts → Use vector_search
- "supernatural" as a title → Use query
- "supernatural movies" (theme) → Use vector_search

RESPONSE RULES:
1. Execute the tool immediately - no explanation beforehand
2. If query returns empty: State "No results found" - do NOT offer alternatives unprompted
3. Present results clearly in bullet points
4. Be concise - no verbose explanations
5. Format output as:
   - Movie: [title] ([year])
   - Director: [name]
   - Actors: [list]
   - Plot: [summary]


"""

# ---------------------------
# Tool setup (BIND TOOLS - THIS WAS MISSING!)
# ---------------------------
tools = [graph_query, vector_search]
llm_with_tools = llm.bind_tools(tools)  # ← YOU NEED THIS!

# ---------------------------
# Agent state definition
# ---------------------------
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]

# ---------------------------
# Agent node (IMPROVED)
# ---------------------------
def agent_node(state: AgentState):
    messages = state["messages"]
    
    # Always include system prompt for context
    messages_with_system = [SystemMessage(content=system_prompt)] + messages
    
    # Use llm_with_tools instead of plain llm
    response = llm_with_tools.invoke(messages_with_system)
    return {"messages": [response]}

# ---------------------------
# Tool node
# ---------------------------
tool_node = ToolNode(tools)

# ---------------------------
# Routing logic
# ---------------------------
def should_continue(state: AgentState):
    last_msg = state["messages"][-1]
    return "tools" if getattr(last_msg, "tool_calls", None) else END

# ---------------------------
# Build the graph workflow
# ---------------------------
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
workflow.add_edge("tools", "agent")
app = workflow.compile()

# ---------------------------
# Helper function to run queries
# ---------------------------
def run_query(query: str):
    """Run query and return final answer only"""
    initial_state = {"messages": [HumanMessage(content=query)]}
    final_state = app.invoke(initial_state)
    final_msg = final_state["messages"][-1]
    return getattr(final_msg, "content", None)


def run_query_with_tools(query: str):
    """
    Run query and return both answer and tools used
    
    Returns:
        tuple: (answer: str, tools_used: list)
    """
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    # Track all tool calls
    tools_used = []
    
    # Stream to capture tool calls
    for output in app.stream(initial_state):
        for node_name, node_output in output.items():
            if "messages" in node_output:
                last_msg = node_output["messages"][-1]
                tool_calls = getattr(last_msg, "tool_calls", None)
                
                if tool_calls:
                    for tool_call in tool_calls:
                        tools_used.append({
                            "tool_name": tool_call.get("name"),
                            "arguments": tool_call.get("args"),
                            "id": tool_call.get("id")
                        })
    
    # Get final answer
    final_state = app.invoke(initial_state)
    final_msg = final_state["messages"][-1]
    answer = getattr(final_msg, "content", None)
    
    return answer, tools_used



def run_query_debug(query: str):
    """Run query with debug output"""
    initial_state = {"messages": [HumanMessage(content=query)]}
    
    print("=== DEBUG MODE ===\n")
    for output in app.stream(initial_state):
        for node_name, node_output in output.items():
            if "messages" in node_output:
                last_msg = node_output["messages"][-1]
                content = getattr(last_msg, "content", None)
                tool_calls = getattr(last_msg, "tool_calls", None)
                
                print(f"--- Node: {node_name} ---")
                if content:
                    print(f"Content: {content[:200]}...")
                if tool_calls:
                    print(f"Tool Calls: {tool_calls}")
                print()
    
    # Return final result
    final_state = app.invoke(initial_state)
    final_msg = final_state["messages"][-1]
    return getattr(final_msg, "content", None)

# ---------------------------
# System evaluation 
# ---------------------------
if __name__ == "__main__":

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


   